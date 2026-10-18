from datetime import date, timedelta

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.core import clock
from apps.core.models import GymScoped


class Expense(GymScoped):
    CATEGORIES = [(c.lower(), c) for c in ("Rent", "Salaries", "Utilities", "Equipment", "Maintenance", "Supplies", "Marketing", "Other")]
    METHODS = [("cash", "Cash"), ("upi", "UPI"), ("card", "Card"), ("bank", "Bank transfer")]
    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="expenses")
    category = models.CharField(max_length=12, choices=CATEGORIES)
    amount_paise = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=METHODS)
    paid_to = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=200, blank=True)
    spent_on = models.DateField(default=timezone.localdate)
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    account = models.ForeignKey("finance.Account", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses",
                                help_text="Where the money came from, set when it is paid: the branch's cash, or its bank account")

    class Meta:
        ordering = ["-spent_on", "-created_at"]
        indexes = [models.Index(fields=["gym", "spent_on"], name="expense_gym_spent_on")]


class RecurringExpense(GymScoped):
    """A bill the gym pays again and again: rent, electricity, a software subscription.

    `starts` is the first date it is due; later dates keep the same day (rent due on the 5th stays on the 5th).
    Each date becomes an ExpenseDue, which paying turns into an ordinary Expense. Never deleted: stopped instead.
    """

    WEEKLY, MONTHLY, QUARTERLY, YEARLY = "weekly", "monthly", "quarterly", "yearly"
    FREQUENCIES = [(WEEKLY, "Every week"), (MONTHLY, "Every month"), (QUARTERLY, "Every 3 months"), (YEARLY, "Every year")]
    MONTHS = {MONTHLY: 1, QUARTERLY: 3, YEARLY: 12}

    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="recurring_expenses")
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=12, choices=Expense.CATEGORIES)
    amount_paise = models.PositiveIntegerField(help_text="What it usually costs; each payment can differ (a bill that varies)")
    method = models.CharField(max_length=8, choices=Expense.METHODS, help_text="How it is usually paid")
    paid_to = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=200, blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    starts = models.DateField(help_text="The first date it is due")
    ends = models.DateField(null=True, blank=True, help_text="The last date it can be due; empty means it keeps going")
    remind_days = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(30)], help_text="How many days before it is due it shows on Home")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["gym", "is_active"], name="recurring_gym_active")]

    def __str__(self):
        return self.name

    def due_dates(self, after: date | None, until: date) -> list[date]:
        """The dates it is due after `after` (exclusive; None means from the start) up to `until`, within its end."""
        last = min(until, self.ends) if self.ends else until
        out, k = [], 0
        while True:
            # Counted from `starts` each time, not from the last date: a bill on the 31st comes back on the 31st
            # after a short month instead of drifting to the 28th.
            d = self.starts + timedelta(weeks=k) if self.frequency == self.WEEKLY else clock.add_months(self.starts, k * self.MONTHS[self.frequency])
            if d > last:
                return out
            if after is None or d > after:
                out.append(d)
            k += 1


class ExpenseDue(GymScoped):
    """One date a recurring expense is owed. Paying it writes the Expense; skipping says it won't be paid."""

    DUE, PAID, SKIPPED = "due", "paid", "skipped"
    STATUSES = [(DUE, "Due"), (PAID, "Paid"), (SKIPPED, "Skipped")]

    recurring = models.ForeignKey(RecurringExpense, on_delete=models.PROTECT, related_name="dues")
    due_on = models.DateField()
    remind_on = models.DateField(help_text="From this day it shows on Home: due_on less the reminder days")
    amount_paise = models.PositiveIntegerField(help_text="Expected amount, from the recurring expense")
    status = models.CharField(max_length=8, choices=STATUSES, default=DUE)
    expense = models.OneToOneField(Expense, null=True, blank=True, on_delete=models.PROTECT, related_name="due")

    class Meta:
        ordering = ["due_on", "id"]
        constraints = [models.UniqueConstraint(fields=["recurring", "due_on"], name="one_due_per_recurring_date")]
        indexes = [models.Index(fields=["gym", "status", "remind_on"], name="expensedue_gym_status_remind")]
