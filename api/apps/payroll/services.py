"""Payroll: working out a month's pay from salary rules and staff check-ins, approving it, and paying it."""
import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Count, F
from django.utils import timezone

from apps.attendance.models import CheckIn
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.expenses.models import Expense
from apps.gyms.models import GymRole

from .models import Payslip, PayslipLine, SalaryPayment, SalaryRule

DAYS = list(calendar.day_name)  # "Monday" … "Sunday", as GymRole.day_off stores them
ADDITIONS = (PayslipLine.ALLOWANCE, PayslipLine.INCENTIVE, PayslipLine.REFERRAL)


def month_label(month: date) -> str:
    return f"{calendar.month_name[month.month]} {month.year}"


def working_days(month: date, day_off: str = "") -> int:
    """Days in the month less each of their weekly day off: 26 in a 30-day month with Sundays off, give or take."""
    total = calendar.monthrange(month.year, month.month)[1]
    if day_off not in DAYS:
        return total
    off = DAYS.index(day_off)
    return total - sum(1 for d in range(1, total + 1) if date(month.year, month.month, d).weekday() == off)


def pay_for(pay_type: str, rate_paise: int, hours_per_day: Decimal, present: int, working: int) -> int:
    """What the days earn, in paise, rounded to the whole rupee (half a rupee rounds up): salaries are paid in rupees.

    A monthly salary by attendance is the salary times days present over working days, never more than the salary:
    a day worked on a day off is paid as an incentive line, which the admin decides.
    """
    if pay_type == SalaryRule.FIXED:
        return rate_paise
    if pay_type == SalaryRule.ATTENDANCE:
        if not working:
            return 0
        share = Decimal(rate_paise) * min(present, working) / working
    elif pay_type == SalaryRule.DAILY:
        share = Decimal(rate_paise) * present
    else:
        share = Decimal(rate_paise) * Decimal(hours_per_day) * present
    return int((share / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)) * 100


def days_present(gym, month: date, staff_ids) -> dict[int, int]:
    """Each person's check-in days in the month: one query. A check-in is one per person per day already."""
    last = date(month.year, month.month, calendar.monthrange(month.year, month.month)[1])
    rows = CheckIn.objects.filter(gym=gym, staff_id__in=staff_ids, local_date__range=(month, last)).values_list("staff_id").annotate(n=Count("id")).order_by()
    return dict(rows)


def recompute(slip: Payslip, lines=None, strict: bool = True) -> Payslip:
    """Write the payslip's totals from its pay and lines. The pay can never fall below what is already paid.

    `strict` is for an admin's change: a deduction bigger than the pay is refused. Working payroll out is not
    strict, because a month's fixed deductions can outweigh a few days present; the net stops at zero instead and
    the payslip shows why.
    """
    lines = list(slip.lines.all()) if lines is None else lines
    slip.pay_paise = pay_for(slip.pay_type, slip.rate_paise, slip.hours_per_day, slip.days_present, slip.working_days)
    slip.additions_paise = sum(x.amount_paise for x in lines if x.kind in ADDITIONS)
    slip.deductions_paise = sum(x.amount_paise for x in lines if x.kind == PayslipLine.DEDUCTION)
    gross = slip.pay_paise + slip.additions_paise
    if strict and slip.deductions_paise > gross:
        raise RuleBroken("deductions_too_high", f"Deductions can't be more than the pay of {rupees(gross)}")
    slip.net_paise = max(gross - slip.deductions_paise, 0)
    paid = slip.paid_paise()
    if slip.net_paise < paid:
        raise RuleBroken("below_paid", f"{rupees(paid)} is already paid, so the salary can't be less than that")
    return slip


def _refresh_draft(slip: Payslip, rule: SalaryRule, present: int) -> None:
    """Bring a draft up to date with the rule and attendance. Lines an admin added stay; rule lines are rewritten."""
    slip.branch_id, slip.pay_type, slip.rate_paise, slip.hours_per_day = rule.branch_id, rule.pay_type, rule.rate_paise, rule.hours_per_day
    slip.working_days = working_days(slip.month, rule.staff.day_off)
    if not slip.days_set_by_hand:
        slip.days_present = present
    slip.lines.filter(from_rule=True).delete()
    PayslipLine.objects.bulk_create([
        PayslipLine(payslip=slip, kind=PayslipLine.ALLOWANCE if i.kind == i.ALLOWANCE else PayslipLine.DEDUCTION, label=i.label, amount_paise=i.amount_paise, from_rule=True)
        for i in rule.items.all()
    ])
    recompute(slip, strict=False)
    slip.save()


@transaction.atomic
def generate(gym, month: date) -> list[Payslip]:
    """Make or refresh the month's payslips for every active staff member with a salary rule.

    Drafts follow the latest rules and check-ins; approved payslips are left exactly as approved. A few queries
    per staff member (their lines), which is fine for a gym's staff of tens; members are never walked.
    """
    if month > clock.today(gym).replace(day=1):
        raise RuleBroken("future_month", "You can work out pay up to this month, not for months still to come")
    rules = list(SalaryRule.objects.filter(gym=gym, staff__is_active=True).select_related("staff").prefetch_related("items"))
    present = days_present(gym, month, [r.staff_id for r in rules])
    # Locked without with_paid(): Postgres refuses FOR UPDATE on a grouped query. recompute asks for the paid total.
    existing = {s.staff_id: s for s in Payslip.objects.select_for_update().filter(gym=gym, month=month)}
    for rule in rules:
        slip = existing.get(rule.staff_id)
        if slip is None:
            slip = Payslip.objects.create(gym=gym, staff=rule.staff, branch_id=rule.branch_id, month=month, pay_type=rule.pay_type,
                                          rate_paise=rule.rate_paise, working_days=0, days_present=0)
            existing[rule.staff_id] = slip
        if slip.status == Payslip.DRAFT:
            try:
                with transaction.atomic():  # a savepoint: one payslip that can't change leaves the rest working
                    _refresh_draft(slip, rule, present.get(rule.staff_id, 0))
            except RuleBroken:
                # More is already paid than the new figures give (a daily wage paid ahead, then the rate cut):
                # this draft stays as it was, for the admin to correct by hand.
                slip.refresh_from_db()
    return list(existing.values())


def salaries_owed(gym, branch: int | None = None) -> dict:
    """Approved salaries not yet paid in full: how many and how much is left. Home and the Dues screen share it.
    Summed in Python over one row per unpaid payslip (Django can't sum an aggregate); a gym has tens of staff."""
    qs = Payslip.objects.filter(gym=gym, status=Payslip.APPROVED).with_paid().filter(net_paise__gt=F("paid_total"))
    if branch is not None:
        qs = qs.filter(branch_id=branch)
    rows = list(qs.values_list("net_paise", "paid_total"))
    return {"count": len(rows), "total_paise": sum(net - paid for net, paid in rows)}


def _locked(slip: Payslip) -> Payslip:
    """The payslip, fresh under a lock: one change at a time, and paid_paise() counts the payments now."""
    return Payslip.objects.select_for_update(of=("self",)).select_related("staff__user").get(pk=slip.pk)


def _draft(slip: Payslip) -> Payslip:
    slip = _locked(slip)
    if slip.status != Payslip.DRAFT:
        raise RuleBroken("approved", "This salary is approved. Reopen it to change it.")
    return slip


@transaction.atomic
def set_days(slip: Payslip, present: int) -> Payslip:
    """An admin's count of days present: for a day they worked without checking in, or a paid leave."""
    slip = _draft(slip)
    if present > calendar.monthrange(slip.month.year, slip.month.month)[1]:
        raise RuleBroken("too_many_days", f"{month_label(slip.month)} has fewer days than that")
    slip.days_present, slip.days_set_by_hand = present, True
    recompute(slip)
    slip.save()
    return slip


@transaction.atomic
def add_line(slip: Payslip, kind: str, label: str, amount_paise: int) -> Payslip:
    slip = _draft(slip)
    line = PayslipLine(payslip=slip, kind=kind, label=label, amount_paise=amount_paise)
    recompute(slip, list(slip.lines.all()) + [line])
    line.save()
    slip.save()
    return slip


@transaction.atomic
def remove_line(slip: Payslip, line_id: int) -> Payslip:
    slip = _draft(slip)
    line = slip.lines.filter(pk=line_id).first()
    if line is None:
        raise RuleBroken("no_line", "That line isn't on this payslip")
    recompute(slip, [x for x in slip.lines.all() if x.pk != line.pk])
    line.delete()
    slip.save()
    return slip


@transaction.atomic
def approve(slip: Payslip, by: GymRole) -> Payslip:
    slip = _draft(slip)
    slip.status, slip.approved_by, slip.approved_at = Payslip.APPROVED, by, timezone.now()
    slip.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return slip


@transaction.atomic
def reopen(slip: Payslip) -> Payslip:
    """Back to a draft, to correct it. Payments made stay, and the pay can't drop below them."""
    slip = _locked(slip)
    if slip.status != Payslip.APPROVED:
        raise RuleBroken("not_approved", "This salary is still a draft")
    slip.status, slip.approved_by, slip.approved_at = Payslip.DRAFT, None, None
    slip.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return slip


@transaction.atomic
def pay(slip: Payslip, *, amount_paise: int, method: str, paid_on: date, by: GymRole, note: str = "") -> SalaryPayment:
    """Pay all or part of a salary. Monthly salaries are approved first; daily wages can be paid as the days go."""
    slip = _locked(slip)
    name = slip.staff.user.name
    if slip.status == Payslip.DRAFT and slip.pay_type != SalaryRule.DAILY:
        raise RuleBroken("not_approved", "Approve this salary before paying it")
    if amount_paise <= 0:
        raise RuleBroken("amount_invalid", "Enter an amount above zero")
    owed = slip.net_paise - slip.paid_paise()
    if amount_paise > owed:
        if owed == 0:
            raise RuleBroken("nothing_due", f"{name}'s salary for {month_label(slip.month)} is paid in full")
        raise RuleBroken("overpaid", f"{name} is owed {rupees(owed)}. Pay that or less.")
    expense = Expense.objects.create(
        gym=slip.gym, branch_id=slip.branch_id, category="salaries", amount_paise=amount_paise, method=method, paid_to=name,
        note=(note or f"Salary, {month_label(slip.month)}")[:200], spent_on=paid_on, created_by=by,
    )
    return SalaryPayment.objects.create(gym=slip.gym, payslip=slip, amount_paise=amount_paise, method=method, paid_on=paid_on, note=note, paid_by=by, expense=expense)
