from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.core.models import GymScoped, TimeStamped
from apps.expenses.models import Expense


class SalaryRule(GymScoped):
    """How one staff member is paid: the pay type and its rate, and fixed monthly allowances and deductions.

    Hours are never measured (the gym records check-in time only), so hourly pay counts the hours of their shift
    on each day they checked in.
    """

    FIXED, ATTENDANCE, HOURLY, DAILY = "fixed", "attendance", "hourly", "daily"
    PAY_TYPES = [
        (FIXED, "Fixed monthly salary"),
        (ATTENDANCE, "Monthly salary, by days present"),
        (HOURLY, "By the hour"),
        (DAILY, "By the day"),
    ]

    staff = models.OneToOneField("gyms.GymRole", on_delete=models.PROTECT, related_name="salary_rule")
    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="+", help_text="The branch whose expenses their pay goes to")
    pay_type = models.CharField(max_length=10, choices=PAY_TYPES)
    rate_paise = models.PositiveIntegerField(help_text="The monthly salary, or the rate for an hour or a day")
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal(0), validators=[MinValueValidator(Decimal(0)), MaxValueValidator(Decimal(24))],
                                        help_text="Hourly pay only: the hours of their shift")

    def __str__(self):
        return f"{self.staff} · {self.get_pay_type_display()}"


class SalaryItem(models.Model):
    """An allowance or deduction paid every month on top of the pay: travel allowance, PF, a loan repayment."""

    ALLOWANCE, DEDUCTION = "allowance", "deduction"
    KINDS = [(ALLOWANCE, "Allowance"), (DEDUCTION, "Deduction")]

    rule = models.ForeignKey(SalaryRule, on_delete=models.CASCADE, related_name="items")
    kind = models.CharField(max_length=10, choices=KINDS)
    label = models.CharField(max_length=60)
    amount_paise = models.PositiveIntegerField()

    class Meta:
        ordering = ["kind", "id"]


class PayslipQuerySet(models.QuerySet):
    def with_paid(self):
        """Each payslip's paid total in the same query, so lists never ask per row."""
        return self.annotate(paid_total=Coalesce(Sum("payments__amount_paise"), 0))


class Payslip(GymScoped):
    """One staff member's pay for one month: the rule as it stood, their days, the lines on top, and what's paid.

    A draft follows attendance until an admin approves it; approved, it is fixed. The totals are stored, written
    by `services.recompute`, so lists and Home can sum them in the database.
    """

    DRAFT, APPROVED = "draft", "approved"
    STATUSES = [(DRAFT, "Draft"), (APPROVED, "Approved")]

    staff = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="payslips")
    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="+")
    month = models.DateField(help_text="The first day of the month it pays for")
    pay_type = models.CharField(max_length=10, choices=SalaryRule.PAY_TYPES)
    rate_paise = models.PositiveIntegerField()
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal(0))
    working_days = models.PositiveSmallIntegerField(help_text="Days in the month less their weekly day off")
    days_present = models.PositiveSmallIntegerField(help_text="Days they checked in, unless an admin set it")
    days_set_by_hand = models.BooleanField(default=False)
    pay_paise = models.PositiveIntegerField(default=0, help_text="Earned from the pay type and days, before lines")
    additions_paise = models.PositiveIntegerField(default=0, help_text="Allowances, incentives and referral bonuses")
    deductions_paise = models.PositiveIntegerField(default=0)
    net_paise = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUSES, default=DRAFT)
    approved_by = models.ForeignKey("gyms.GymRole", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = PayslipQuerySet.as_manager()

    class Meta:
        ordering = ["-month", "staff__user__name", "id"]
        constraints = [models.UniqueConstraint(fields=["staff", "month"], name="one_payslip_per_staff_month")]
        indexes = [models.Index(fields=["gym", "month"], name="payslip_gym_month"), models.Index(fields=["gym", "status"], name="payslip_gym_status")]

    def paid_paise(self) -> int:
        if hasattr(self, "paid_total"):
            return self.paid_total
        return self.payments.aggregate(t=Sum("amount_paise"))["t"] or 0


class PayslipLine(TimeStamped):
    """Something added to or taken from one month's pay. Lines from the rule follow it while the payslip is a draft."""

    ALLOWANCE, INCENTIVE, REFERRAL, DEDUCTION = "allowance", "incentive", "referral", "deduction"
    KINDS = [(ALLOWANCE, "Allowance"), (INCENTIVE, "Incentive"), (REFERRAL, "Referral bonus"), (DEDUCTION, "Deduction")]

    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name="lines")
    kind = models.CharField(max_length=10, choices=KINDS)
    label = models.CharField(max_length=60)
    amount_paise = models.PositiveIntegerField()
    from_rule = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]


class SalaryPayment(GymScoped):
    """Money paid against a payslip, in full or in part. Each one is also an expense under Salaries."""

    payslip = models.ForeignKey(Payslip, on_delete=models.PROTECT, related_name="payments")
    amount_paise = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=Expense.METHODS)
    paid_on = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    paid_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, related_name="salary_payment")

    class Meta:
        ordering = ["-paid_on", "-id"]
