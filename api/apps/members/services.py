"""Selling plans and taking money: the rules the desk works by, kept out of the views so tests and the seed share them."""
from datetime import timedelta

from django.db import transaction

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees

from .models import Member, Payment, Subscription


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
    if offer is not None:
        if offer.gym_id != member.gym_id or not offer.applies_to(plan, today):
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
    return Payment.objects.create(
        gym=member.gym,
        member=member,
        subscription=subscription,
        branch=branch or member.home_branch,
        amount_paise=amount_paise,
        method=method,
        taken_by=by,
        note=note,
    )


def next_code(gym):
    """Member IDs like RF-1001: two letters from the gym, then a running number."""
    prefix = "".join(w[0] for w in gym.name.split()[:2]).upper() or "M"
    nums = [int(c.rsplit("-", 1)[-1]) for c in Member.objects.filter(gym=gym, code__startswith=prefix + "-").values_list("code", flat=True) if c.rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}-{max(nums, default=1000) + 1}"
