"""The rules of a gym's Rackline plan: its prices, its branch quota and the requests for more branches.

Anything that opens a branch or changes a quota locks the gym's `GymBilling` row first, so two at once can't both
squeeze into the last free branch.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.gyms.models import Branch, Gym, GymRole

from .models import LAST_BILLING_DAY, BranchRequest, GymBilling, InvoiceLine, PriceList


def branches_label(n: int) -> str:
    return f"{n} branch" if n == 1 else f"{n} branches"


def locked_plan(gym: Gym) -> GymBilling:
    plan = GymBilling.objects.select_for_update().filter(gym=gym).first()
    if plan is None:  # a gym made by hand in the Django admin, not by create_gym
        raise RuleBroken("no_plan", "This gym has no Rackline plan yet. Ask Rackline to set it up.")
    return plan


def active_branches(gym: Gym, leaving_out: Branch | None = None) -> int:
    qs = Branch.objects.filter(gym=gym, is_active=True)
    return (qs.exclude(pk=leaving_out.pk) if leaving_out is not None else qs).count()


# Prices

@transaction.atomic
def add_price_list(*, active_from: date, prices: dict, note: str = "", by=None) -> PriceList:
    """New prices from a day on, today or later. Gyms keep theirs until a Rackline admin moves them."""
    if active_from < timezone.localdate():
        raise RuleBroken("past_date", "New prices start today or later. Gyms already billed keep what they were billed.")
    try:
        with transaction.atomic():
            return PriceList.objects.create(active_from=active_from, note=note.strip(), created_by=by, **prices)
    except IntegrityError:
        raise RuleBroken("date_taken", f"Another price list already starts on {clock.date_label(active_from)} {active_from.year}. Pick another day.")


def open_plan(gym: Gym, *, quota: int = 1, billing_day: int | None = None) -> GymBilling:
    """A new gym's Rackline plan, on today's prices. Called inside `create_gym`'s transaction."""
    prices = PriceList.current()
    if prices is None:
        raise RuleBroken("no_prices", "Rackline has no prices yet. Add a price list in Prices first.")
    day = billing_day or min(clock.today(gym).day, LAST_BILLING_DAY)
    return GymBilling.objects.create(gym=gym, price_list=prices, branch_quota=quota, billing_day=day, **prices.prices())


@transaction.atomic
def change_plan(gym: Gym, *, branch_quota: int | None = None, billing_day: int | None = None, whatsapp_mode: str | None = None) -> GymBilling:
    """A Rackline admin setting the quota, billing day or WhatsApp mode. A quota never drops below the branches open."""
    plan = locked_plan(gym)
    if branch_quota is not None and branch_quota != plan.branch_quota:
        open_now = active_branches(gym)
        if branch_quota < open_now:
            raise RuleBroken("below_branches", f"{gym.name} has {branches_label(open_now)} open. Its plan can't have room for fewer.")
        plan.branch_quota = branch_quota
    if billing_day is not None:
        plan.billing_day = billing_day
    if whatsapp_mode is not None:
        plan.whatsapp_mode = whatsapp_mode
    plan.save()
    return plan


@transaction.atomic
def move_to_current_prices(gym: Gym) -> GymBilling:
    """Copy today's price list onto the gym's plan. Its next invoice uses them; past invoices never change."""
    plan = locked_plan(gym)
    prices = PriceList.current()
    if prices is None or prices.pk == plan.price_list_id:
        raise RuleBroken("already_current", f"{gym.name} is already on the current prices")
    plan.price_list = prices
    for f, v in prices.prices().items():
        setattr(plan, f, v)
    plan.save()
    return plan


# The branch quota

def make_room_for_branch(gym: Gym, branch: Branch | None = None) -> None:
    """Call inside the transaction that opens a branch (or reopens `branch`): refused when the plan is full."""
    plan = locked_plan(gym)
    if active_branches(gym, leaving_out=branch) >= plan.branch_quota:
        raise RuleBroken("branch_limit", f"Your plan has room for {branches_label(plan.branch_quota)}. Ask for another one to open this branch.")


# Asking for more branches

@transaction.atomic
def ask_for_branches(gym: Gym, *, count: int, note: str, by) -> BranchRequest:
    """Add Branch to My Plan: one open request at a time, so Rackline answers one question per gym."""
    locked_plan(gym)
    if BranchRequest.objects.filter(gym=gym, status=BranchRequest.ASKED).exists():
        raise RuleBroken("already_asked", "You've already asked for more branches. Rackline will answer soon.")
    return BranchRequest.objects.create(gym=gym, count=count, note=note.strip(), asked_by=by)


@dataclass
class ProRata:
    charged_from: date
    charged_to: date
    period_days: int
    rate_paise: int
    amount_paise: int

    @property
    def days(self) -> int:
        return (self.charged_to - self.charged_from).days + 1


def billing_month(billing_day: int, on: date) -> tuple[date, date]:
    """The billing month `on` falls in: from the last billing day to the day before the next one."""
    starts = on.replace(day=billing_day) if on.day >= billing_day else clock.add_months(on, -1).replace(day=billing_day)
    return starts, clock.add_months(starts, 1) - timedelta(days=1)


def pro_rata(per_branch_paise: int, count: int, billing_day: int, on: date) -> ProRata:
    """What `count` more branches cost from `on` to the end of its billing month: the per-branch fee × days left ÷
    days in the month, rounded to the rupee (half up)."""
    starts, ends = billing_month(billing_day, on)
    period, left = (ends - starts).days + 1, (ends - on).days + 1
    rupees = (per_branch_paise * count * left + 50 * period) // (100 * period)
    return ProRata(on, ends, period, per_branch_paise, rupees * 100)


def _decided(req: BranchRequest, by) -> BranchRequest:
    req = BranchRequest.objects.select_for_update().get(pk=req.pk)
    if req.status != BranchRequest.ASKED:
        raise RuleBroken("decided", f"This request was already {req.get_status_display().lower()}")
    if GymRole.objects.filter(gym=req.gym_id, user=by, is_active=True).exists():
        raise RuleBroken("own_gym", "You work at this gym, so another Rackline admin decides its requests")
    req.decided_by, req.decided_at = by, timezone.now()
    return req


@transaction.atomic
def approve(req: BranchRequest, *, by) -> BranchRequest:
    """Raise the quota now and keep what the rest of this billing month costs, for the next invoice."""
    plan = locked_plan(req.gym)
    req = _decided(req, by)
    cost = pro_rata(plan.per_branch_paise, req.count, plan.billing_day, clock.today(req.gym))
    plan.branch_quota += req.count
    plan.save(update_fields=["branch_quota", "updated_at"])
    req.status = BranchRequest.APPROVED
    req.charged_from, req.charged_to, req.period_days = cost.charged_from, cost.charged_to, cost.period_days
    req.rate_paise, req.pro_rata_paise = cost.rate_paise, cost.amount_paise
    req.save()
    pro_rata_line(req)
    return req


def pro_rata_line(req: BranchRequest) -> InvoiceLine:
    """The pending line that bills an approved request on the gym's next invoice: how many, which days, and why."""
    return InvoiceLine.objects.create(
        gym_id=req.gym_id, kind=InvoiceLine.BRANCHES_PRO_RATA, branch_request=req, starts=req.charged_from, ends=req.charged_to,
        description=f"{branches_label(req.count)} added, {clock.date_label(req.charged_from)} to {clock.date_label(req.charged_to)} "
                    f"({req.days_charged} of {req.period_days} days)",
        quantity=req.count, rate_paise=req.rate_paise, amount_paise=req.pro_rata_paise, added_by=req.decided_by,
    )


@transaction.atomic
def decline(req: BranchRequest, *, by, reason: str) -> BranchRequest:
    locked_plan(req.gym)
    req = _decided(req, by)
    req.status, req.decline_reason = BranchRequest.DECLINED, reason.strip()
    req.save()
    return req
