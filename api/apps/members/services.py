"""Selling plans and taking money: the rules the desk works by, kept out of the views so tests and the seed share them."""
from datetime import timedelta

from django.db import transaction

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.finance.models import Account, StatementTick
from apps.finance.services import before_change
from apps.messages.notify import after_commit
from apps.messages.tasks import send_payment_receipt

from .models import Member, Payment, Refund, Subscription, sold_at


def next_start(member: Member, today):
    """A renewal starts the day after the current plan ends, or today if it has already ended."""
    last = member.subscriptions.filter(cancelled=False).order_by("-ends").first()
    if last and last.ends >= today:
        return last.ends + timedelta(days=1)
    return today


@transaction.atomic
def sell(member, plan, by, offer=None, starts=None):
    today = clock.today(member.gym)
    if plan.gym_id != member.gym_id or not plan.on_sale:
        raise RuleBroken("plan_not_on_sale", f"{plan.name} isn't on sale")
    branch = member.home_branch
    if not sold_at(plan, branch):
        raise RuleBroken("plan_not_at_branch", f"{plan.name} isn't sold at {branch.name}")
    if offer is not None:
        if offer.gym_id != member.gym_id or not offer.applies_to(plan, today, branch):
            raise RuleBroken("offer_not_valid", f"{offer.name} doesn't apply to {plan.name} today")
    starts = starts or next_start(member, today)
    discount = offer.discount_on(plan.price_paise) if offer else 0
    return Subscription.objects.create(
        member=member,
        plan=plan,
        starts=starts,
        ends=clock.plan_end(starts, plan.months),
        list_price_paise=plan.price_paise,
        offer=offer,
        price_paise=plan.price_paise - discount,
        sold_by=by,
    )


@transaction.atomic
def take_payment(member, amount_paise, method, by, branch=None, subscription=None, note=""):
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
    after_commit(send_payment_receipt, payment.pk)  # the member's receipt, if the gym sends them
    return payment


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


def next_code(gym):
    """Member IDs like RF-1001: two letters from the gym, then a running number."""
    prefix = "".join(w[0] for w in gym.name.split()[:2]).upper() or "M"
    nums = [int(c.rsplit("-", 1)[-1]) for c in Member.objects.filter(gym=gym, code__startswith=prefix + "-").values_list("code", flat=True) if c.rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}-{max(nums, default=1000) + 1}"
