"""Selling plans and taking money: the rules the desk works by, kept out of the views so tests and the seed share them."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.finance.models import Account, StatementTick
from apps.finance.services import before_change
from apps.messages.notify import after_commit
from apps.messages.tasks import send_payment_receipt

from apps.gyms.models import GymRole

from .models import Member, Payment, Plan, PTSession, Refund, Subscription, sold_at


def next_start(member: Member, today, kind=Plan.MEMBERSHIP):
    """A renewal starts the day after the current plan of its kind ends, or today if it has already ended."""
    last = member.subscriptions.filter(cancelled=False, plan__kind=kind).order_by("-ends").first()
    if last and last.ends >= today:
        return last.ends + timedelta(days=1)
    return today


def membership_on(member: Member, day) -> bool:
    return member.subscriptions.filter(cancelled=False, plan__kind=Plan.MEMBERSHIP, starts__lte=day, ends__gte=day).exists()


def needs_membership(member: Member, plan: Plan, starts):
    """At a gym that sells personal training only on top of a membership, it starts on a day a membership covers."""
    if plan.kind == Plan.PT and member.gym.pt_needs_membership and not membership_on(member, starts):
        raise RuleBroken("membership_needed", f"{member.name} has no membership on {_day(starts)}. Sell them a membership first, "
                                              "or start personal training on a day their membership covers.")


def no_overlap(member, kind, starts, ends, exclude=None):
    """A member's plans of one kind (memberships, personal training) never run on the same day twice."""
    clash = (member.subscriptions.filter(cancelled=False, plan__kind=kind, starts__lte=ends, ends__gte=starts)
             .exclude(pk=exclude).select_related("plan").first())
    if clash:
        raise RuleBroken("plans_overlap", f"These dates overlap {clash.plan.name}, {_day(clash.starts)} to {_day(clash.ends)}. Pick dates around it.")


def _day(d):
    return clock.date_label(d)


@transaction.atomic
def sell(member, plan, by, offer=None, starts=None, ends=None, trainer=None):
    """A plan sold to a member. Personal training takes its sessions from the plan and its trainer from `trainer`
    (who becomes the member's trainer) or the member's own."""
    today = clock.today(member.gym)
    if plan.gym_id != member.gym_id or not plan.on_sale:
        raise RuleBroken("plan_not_on_sale", f"{plan.name} isn't on sale")
    branch = member.home_branch
    if not sold_at(plan, branch):
        raise RuleBroken("plan_not_at_branch", f"{plan.name} isn't sold at {branch.name}")
    if offer is not None:
        if offer.gym_id != member.gym_id or not offer.applies_to(plan, today, branch):
            raise RuleBroken("offer_not_valid", f"{offer.name} doesn't apply to {plan.name} today")
    starts = starts or next_start(member, today, plan.kind)
    ends = ends or clock.plan_end(starts, plan.months, member.gym.month_days)
    if ends < starts:
        raise RuleBroken("dates_invalid", "Pick an end date on or after the start date")
    no_overlap(member, plan.kind, starts, ends)
    needs_membership(member, plan, starts)
    pt = plan.kind == Plan.PT
    trainer = (trainer or member.trainer) if pt else None
    if pt and trainer is not None and member.trainer_id != trainer.id:
        member.trainer = trainer
        member.save(update_fields=["trainer", "updated_at"])
    discount = offer.discount_on(plan.price_paise) if offer else 0
    return Subscription.objects.create(
        member=member,
        plan=plan,
        starts=starts,
        ends=ends,
        list_price_paise=plan.price_paise,
        offer=offer,
        price_paise=plan.price_paise - discount,
        sold_by=by,
        sessions=plan.sessions if pt else 0,
        trainer=trainer,
    )


@transaction.atomic
def correct(sub: Subscription, changes: dict) -> dict:
    """An admin's correction of a plan already sold: its plan, offer, price or dates. A new plan or offer works the price
    out again the way a sale does, and a new plan or start date the end date, unless those are given too. Returns what
    it was before, for the audit log. Money already paid stays with the plan, so the price can't go below it."""
    member = sub.member
    Member.objects.select_for_update().filter(pk=member.pk).first()  # one change at a time per member, as take_payment
    sub = Subscription.objects.select_for_update(of=("self",)).select_related("plan", "offer").get(pk=sub.pk)
    if sub.cancelled:
        raise RuleBroken("cancelled", "This plan is cancelled")
    before = {"plan": sub.plan_id, "offer": sub.offer_id, "starts": str(sub.starts), "ends": str(sub.ends), "price_paise": sub.price_paise,
              "sessions": sub.sessions}
    today, branch = clock.today(member.gym), member.home_branch

    plan = changes.get("plan", sub.plan)
    new_plan = plan.pk != sub.plan_id
    if new_plan and not plan.on_sale:
        raise RuleBroken("plan_not_on_sale", f"{plan.name} isn't on sale")
    if new_plan and not sold_at(plan, branch):
        raise RuleBroken("plan_not_at_branch", f"{plan.name} isn't sold at {branch.name}")
    offer = changes["offer"] if "offer" in changes else sub.offer
    new_offer = (offer.pk if offer else None) != sub.offer_id
    if offer and new_offer and not offer.applies_to(plan, today, branch):
        raise RuleBroken("offer_not_valid", f"{offer.name} doesn't apply to {plan.name} today")
    if offer and new_plan and not new_offer and offer.plans.exists() and not offer.plans.filter(pk=plan.pk).exists():
        raise RuleBroken("offer_not_valid", f"{offer.name} doesn't apply to {plan.name}. Remove the offer or pick another.")

    list_price = plan.price_paise if new_plan else sub.list_price_paise
    if "price_paise" in changes:
        price = changes["price_paise"]
    elif new_plan or new_offer:
        price = list_price - (offer.discount_on(list_price) if offer else 0)
    else:
        price = sub.price_paise
    paid = sub.paid_paise()
    if price < paid:
        raise RuleBroken("price_below_paid", f"{rupees(paid)} has been paid for this plan. Set the price to that or more, or refund first.")

    starts = changes.get("starts", sub.starts)
    if "ends" in changes:
        ends = changes["ends"]
    elif new_plan or starts != sub.starts:
        ends = clock.plan_end(starts, plan.months, member.gym.month_days)
    else:
        ends = sub.ends
    if (starts, ends) != (sub.starts, sub.ends):  # a freeze can already push a plan into the next: only new dates are checked
        if sub.frozen_from:
            raise RuleBroken("frozen", "This plan is frozen. Unfreeze it before changing its dates.")
        if ends < starts:
            raise RuleBroken("dates_invalid", "Pick an end date on or after the start date")
        no_overlap(member, plan.kind, starts, ends, exclude=sub.pk)
    if new_plan or starts != sub.starts:
        needs_membership(member, plan, starts)

    sessions = (plan.sessions if plan.kind == Plan.PT else 0) if new_plan else sub.sessions
    used = sub.sessions_used()
    if sessions < used:
        raise RuleBroken("sessions_below_used", f"{used} sessions have been given on this plan. Pick a plan with that many or more.")
    trainer = (sub.trainer or member.trainer) if plan.kind == Plan.PT else None

    after = {"plan": plan.pk, "offer": offer.pk if offer else None, "starts": str(starts), "ends": str(ends), "price_paise": price, "sessions": sessions}
    if after == before:
        raise RuleBroken("nothing_changed", "Nothing was changed")
    sub.plan, sub.offer, sub.list_price_paise, sub.price_paise, sub.starts, sub.ends = plan, offer, list_price, price, starts, ends
    sub.sessions, sub.trainer = sessions, trainer
    sub.save(update_fields=["plan", "offer", "list_price_paise", "price_paise", "starts", "ends", "sessions", "trainer", "updated_at"])
    return before


@transaction.atomic
def take_payment(member, amount_paise, method, by, branch=None, subscription=None, note="", receipt=True):
    Member.objects.select_for_update().filter(pk=member.pk).first()  # one desk at a time per member
    if amount_paise <= 0:
        raise RuleBroken("amount_invalid", "Enter an amount above zero")
    owed = Member.objects.with_totals().get(pk=member.pk).balance_paise()  # fresh, under the lock
    if amount_paise > owed:
        if owed == 0:
            raise RuleBroken("nothing_due", f"{member.name} has nothing due. Sell a plan first.")
        raise RuleBroken("overpaid", f"{member.name} owes {rupees(owed)}. Take that or less.")
    if subscription is None:
        # oldest subscription that still has money owing
        for sub in member.subscriptions.filter(cancelled=False).order_by("starts").with_paid():
            if sub.paid_paise() < sub.price_paise:
                subscription = sub
                break
    branch = branch or member.home_branch
    payment = Payment.objects.create(
        gym=member.gym,
        member=member,
        subscription=subscription,
        branch=branch,
        amount_paise=amount_paise,
        method=method,
        taken_by=by,
        note=note,
        account=Account.objects.for_money(branch.id, method, on=clock.today(member.gym)),
    )
    if receipt:
        after_commit(send_payment_receipt, payment.pk)  # the member's receipt, if the gym sends them
    return payment


@transaction.atomic
def take_split(member, parts: list[tuple[str, int]], by, branch=None, note="") -> list[Payment]:
    """One amount paid more than one way (₹1,000 in cash and ₹500 by UPI): a payment for each, so every drawer and
    account gets its share, saved together or not at all, and one receipt for the total."""
    methods = [m for m, _ in parts]
    if len(parts) < 2:
        raise RuleBroken("split_too_few", "Split it two ways or more, or take one payment")
    if len(set(methods)) != len(methods):
        raise RuleBroken("split_same_method", "Use each way of paying once")
    Member.objects.select_for_update().filter(pk=member.pk).first()
    total, owed = sum(a for _, a in parts), Member.objects.with_totals().get(pk=member.pk).balance_paise()
    if owed and total > owed:
        raise RuleBroken("overpaid", f"{member.name} owes {rupees(owed)}. The parts add up to {rupees(total)}.")
    payments = [take_payment(member, amount, method, by, branch=branch, note=note, receipt=False) for method, amount in parts]
    after_commit(send_payment_receipt, payments[0].pk, [p.pk for p in payments[1:]])
    return payments


@transaction.atomic
def refund(sub: Subscription, *, amount_paise: int, method: str, reason: str, end_plan: bool, by, branch=None) -> Refund:
    """Give money back for a plan: never more than was paid for it and not refunded yet. With `end_plan` the plan ends
    today, or is cancelled when it hasn't started (then all of it must be refunded, since nothing of it is used).
    The money comes out of the account the branch and method choose; a low balance never stops it."""
    member = sub.member
    Member.objects.select_for_update().filter(pk=member.pk).first()  # one desk at a time per member, as take_payment
    sub = Subscription.objects.select_for_update().get(pk=sub.pk)
    if sub.cancelled:
        raise RuleBroken("cancelled", "This plan is cancelled")
    if amount_paise <= 0:
        raise RuleBroken("amount_invalid", "Enter an amount above zero")
    left = sub.paid_paise() - sub.refunded_paise()
    if left <= 0:
        raise RuleBroken("nothing_paid", "Nothing paid for this plan is left to refund")
    if amount_paise > left:
        raise RuleBroken("more_than_paid", f"{rupees(left)} was paid for this plan and isn't refunded yet. Refund that or less.")
    today = clock.today(member.gym)
    r = Refund(gym=member.gym, member=member, subscription=sub, branch=branch or member.home_branch, amount_paise=amount_paise, method=method,
               reason=reason, refunded_by=by)
    if end_plan and sub.starts > today:
        if amount_paise != left:
            raise RuleBroken("not_started", f"This plan hasn't started. Refund all {rupees(left)} to end it, or keep it.")
        sub.cancelled = r.cancelled_plan = True
        sub.save(update_fields=["cancelled", "updated_at"])
    elif end_plan and sub.ends > today:
        r.ended_plan, r.plan_ended_from = True, sub.ends
        sub.ends = today
        if sub.frozen_from and sub.frozen_from > today:  # a freeze that hadn't started never will
            sub.frozen_from = sub.frozen_until = None
        elif sub.frozen_until and sub.frozen_until > today:
            sub.frozen_until = today
        sub.save(update_fields=["ends", "frozen_from", "frozen_until", "updated_at"])
    r.account = Account.objects.for_money(r.branch_id, method, on=today)
    r.save()
    return r


@transaction.atomic
def void_refund(r: Refund, reason: str) -> Refund:
    """The refund was wrong: the money counts as paid again, and a plan it ended or cancelled is put back."""
    r = Refund.objects.select_for_update().select_related("subscription").get(pk=r.pk)
    if r.voided:
        raise RuleBroken("voided", "This refund is already voided")
    before_change(StatementTick.REFUND, r.pk)
    sub = r.subscription
    if r.cancelled_plan:
        sub.cancelled = False
        sub.save(update_fields=["cancelled", "updated_at"])
    elif r.ended_plan and r.plan_ended_from:
        sub.ends = r.plan_ended_from
        sub.save(update_fields=["ends", "updated_at"])
    r.voided, r.void_reason = True, reason
    r.save(update_fields=["voided", "void_reason", "updated_at"])
    return r


@transaction.atomic
def mark_session(sub: Subscription, by, on=None, body_parts=(), notes="") -> PTSession:
    """A personal training session given on `on` (today when left out): it uses one of the plan's sessions. One a
    day for each plan. At a gym where personal training needs a membership, that day needs one too."""
    member = sub.member
    Member.objects.select_for_update().filter(pk=member.pk).first()  # two taps at once count once
    sub = Subscription.objects.select_related("plan").with_used().get(pk=sub.pk)
    today = clock.today(member.gym)
    on = on or today
    if sub.cancelled or sub.plan.kind != Plan.PT:
        raise RuleBroken("not_pt", "Sessions are marked on personal training plans")
    if on > today:
        raise RuleBroken("day_in_future", "Pick a day that has already come")
    if not sub.starts <= on <= sub.ends:
        raise RuleBroken("outside_plan", f"{sub.plan.name} runs {_day(sub.starts)} to {_day(sub.ends)}. Pick a day inside it.")
    if sub.is_frozen(on):
        raise RuleBroken("frozen", "This plan is frozen on that day. Unfreeze it first.")
    if sub.sessions_left() == 0:
        raise RuleBroken("no_sessions_left", f"All {sub.sessions} sessions are used. Sell a new plan for more.")
    if member.gym.pt_needs_membership and not membership_on(member, on):
        raise RuleBroken("membership_needed", f"{member.name} has no membership on {_day(on)}. Renew it before the next session.")
    if sub.pt_sessions.filter(local_date=on, voided=False).exists():
        raise RuleBroken("session_already_marked", f"{member.name}'s session on {_day(on)} is already marked")
    trainer = by if by.role == GymRole.TRAINER else sub.trainer
    return PTSession.objects.create(gym=member.gym, subscription=sub, member=member, trainer=trainer, local_date=on, marked_by=by,
                                     body_parts=list(body_parts), notes=notes.strip())


@transaction.atomic
def note_session(s: PTSession, body_parts=None, notes=None) -> PTSession:
    """Change what a session worked and its notes; whatever is left out stays. A removed session stays as it was."""
    s = PTSession.objects.select_for_update().get(pk=s.pk)
    if s.voided:
        raise RuleBroken("voided", "This session is removed. Mark it again to add what they worked.")
    if body_parts is not None:
        s.body_parts = list(body_parts)
    if notes is not None:
        s.notes = notes.strip()
    s.save(update_fields=["body_parts", "notes", "updated_at"])
    return s


@transaction.atomic
def void_session(s: PTSession, reason: str, by) -> PTSession:
    """A session marked by mistake: the plan gets it back. Admins remove any; others only one they marked today."""
    s = PTSession.objects.select_for_update().select_related("gym").get(pk=s.pk)
    if s.voided:
        raise RuleBroken("voided", "This session is already removed")
    if by.role != GymRole.ADMIN and (s.marked_by_id != by.id or clock.local(s.gym, s.marked_at).date() != clock.today(s.gym)):
        raise RuleBroken("not_yours", "You can remove a session you marked today. Ask an admin to remove this one.")
    s.voided, s.void_reason, s.voided_by, s.voided_at = True, reason, by, timezone.now()
    s.save(update_fields=["voided", "void_reason", "voided_by", "voided_at", "updated_at"])
    return s


def next_code(gym):
    """Member IDs like RF-1001: two letters from the gym, then a running number."""
    prefix = "".join(w[0] for w in gym.name.split()[:2]).upper() or "M"
    nums = [int(c.rsplit("-", 1)[-1]) for c in Member.objects.filter(gym=gym, code__startswith=prefix + "-").values_list("code", flat=True) if c.rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}-{max(nums, default=1000) + 1}"
