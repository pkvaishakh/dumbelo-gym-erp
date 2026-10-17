"""Recurring expenses: writing down the dates they are due, paying them and skipping them."""
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, Max, Q, Sum

from apps.core import clock
from apps.core.errors import RuleBroken

from .models import Expense, ExpenseDue, RecurringExpense

#: Dues are written this far ahead of their reminder day, so the list shows what is coming next as well.
LOOKAHEAD_DAYS = 31


def sync_dues(gym, today: date | None = None) -> int:
    """Write the dates each running recurring expense is due, up to a month past its reminder. Safe to repeat.

    Called before dues are read (the Dues list, Home) rather than only by a nightly job, so a gym never misses a
    bill because a worker was down. It is three queries for the whole gym: the rules with their last date, then
    one insert.
    """
    today = today or clock.today(gym)
    fresh = []
    for rule in RecurringExpense.objects.filter(gym=gym, is_active=True).annotate(last=Max("dues__due_on")):
        until = today + timedelta(days=rule.remind_days + LOOKAHEAD_DAYS)
        for d in rule.due_dates(rule.last, until):
            fresh.append(ExpenseDue(gym=gym, recurring=rule, due_on=d, remind_on=d - timedelta(days=rule.remind_days), amount_paise=rule.amount_paise))
    # ignore_conflicts: two screens loading at once must not trip over the unique date
    ExpenseDue.objects.bulk_create(fresh, batch_size=500, ignore_conflicts=True)
    return len(fresh)


def reconcile(rule: RecurringExpense, today: date) -> None:
    """After a recurring expense changes: dates still to come follow its new amount and reminder, and dates it no
    longer reaches (it was stopped, or ends sooner) are skipped. Paid and past dates are history and stay."""
    later = ExpenseDue.objects.filter(recurring=rule, status=ExpenseDue.DUE, due_on__gte=today)
    if not rule.is_active:
        later.update(status=ExpenseDue.SKIPPED)
        return
    if rule.ends:
        later.filter(due_on__gt=rule.ends).update(status=ExpenseDue.SKIPPED)
    rows = list(later.filter(status=ExpenseDue.DUE))
    for due in rows:
        due.amount_paise, due.remind_on = rule.amount_paise, due.due_on - timedelta(days=rule.remind_days)
    ExpenseDue.objects.bulk_update(rows, ["amount_paise", "remind_on"], batch_size=500)
    sync_dues(rule.gym, today)


def bills_due(gym, today: date, branch: int | None = None) -> dict:
    """Bills inside their reminder days and not paid or skipped: how many, how many are late, and the amount.
    The same figures on Home and on the Dues screen. Call sync_dues first."""
    qs = ExpenseDue.objects.filter(gym=gym, status=ExpenseDue.DUE, remind_on__lte=today)
    if branch is not None:
        qs = qs.filter(recurring__branch_id=branch)
    agg = qs.aggregate(n=Count("id"), late=Count("id", filter=Q(due_on__lt=today)), t=Sum("amount_paise"))
    return {"count": agg["n"], "overdue": agg["late"], "total_paise": agg["t"] or 0}


@transaction.atomic
def pay_due(due: ExpenseDue, *, amount_paise: int, method: str, paid_on: date, by, note: str = "") -> Expense:
    """Pay one due date: it becomes an ordinary expense of the recurring expense's category and branch."""
    due = ExpenseDue.objects.select_for_update().select_related("recurring").get(pk=due.pk)  # one payment per date
    if due.status != ExpenseDue.DUE:
        raise RuleBroken("not_due", "This one is already paid or skipped")
    if amount_paise <= 0:
        raise RuleBroken("amount_invalid", "Enter an amount above zero")
    rule = due.recurring
    expense = Expense.objects.create(
        gym=due.gym, branch_id=rule.branch_id, category=rule.category, amount_paise=amount_paise, method=method,
        paid_to=rule.paid_to, note=(note or f"{rule.name}, due {clock.date_label(due.due_on)}")[:200], spent_on=paid_on, created_by=by,
    )
    due.status, due.expense = ExpenseDue.PAID, expense
    due.save(update_fields=["status", "expense", "updated_at"])
    return expense


@transaction.atomic
def skip_due(due: ExpenseDue) -> ExpenseDue:
    """This date won't be paid (the landlord waived a month): it leaves the dues list. Nothing is spent."""
    due = ExpenseDue.objects.select_for_update().get(pk=due.pk)
    if due.status != ExpenseDue.DUE:
        raise RuleBroken("not_due", "This one is already paid or skipped")
    due.status = ExpenseDue.SKIPPED
    due.save(update_fields=["status", "updated_at"])
    return due
