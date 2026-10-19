"""What a gym pays Dumbelo: the price list, each gym's Dumbelo plan, the branches it asks to add, and its
invoices and payments.

"Dumbelo plan" in code and copy, never just "plan": `members.Plan` is what a member buys from the gym.
"""
from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.core.models import TimeStamped

# Invoices are written on the billing day, so it stops at 28: every month has one.
LAST_BILLING_DAY = 28


class Prices(models.Model):
    """Dumbelo's prices, all in paise. A price list holds them; each gym's plan keeps its own copy."""

    base_paise = models.PositiveIntegerField(help_text="Monthly base fee")
    per_branch_paise = models.PositiveIntegerField(help_text="Monthly fee for each branch the plan has room for")
    whatsapp_setup_paise = models.PositiveIntegerField(help_text="One time, for setting up WhatsApp")
    machine_setup_paise = models.PositiveIntegerField(help_text="One time, for each attendance machine")
    # A delivered message on Dumbelo's shared number, by Meta's category
    utility_message_paise = models.PositiveIntegerField(help_text="Reminders and receipts (Meta's utility category)")
    marketing_message_paise = models.PositiveIntegerField(help_text="Offers and news (Meta's marketing category)")
    authentication_message_paise = models.PositiveIntegerField(help_text="Sign-in codes (Meta's authentication category)")

    FIELDS = ("base_paise", "per_branch_paise", "whatsapp_setup_paise", "machine_setup_paise", "utility_message_paise",
              "marketing_message_paise", "authentication_message_paise")

    class Meta:
        abstract = True

    def prices(self) -> dict:
        return {f: getattr(self, f) for f in self.FIELDS}


class PriceList(Prices):
    """Dumbelo's prices from a day on. Never changed once added: new prices are a new list. A new list never
    reprices a gym by itself; a Dumbelo admin moves each gym to it."""

    active_from = models.DateField(unique=True)
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-active_from"]

    def __str__(self):
        return f"Prices from {self.active_from}"

    @classmethod
    def current(cls, on=None):
        """The list in force on `on` (Dumbelo's today): the latest one that has started. None before the first."""
        return cls.objects.filter(active_from__lte=on or timezone.localdate()).order_by("-active_from").first()


class GymBilling(Prices, TimeStamped):
    """A gym's Dumbelo plan: its prices (copied from a price list), how many branches it pays for, its billing day
    and how it sends WhatsApp. The monthly charge is the base fee plus the per-branch fee times the quota."""

    SHARED, OWN, OFF = "shared", "own", "off"
    WHATSAPP_MODES = [(SHARED, "Dumbelo's number"), (OWN, "The gym's own number"), (OFF, "Off")]

    gym = models.OneToOneField("gyms.Gym", on_delete=models.CASCADE, related_name="billing")
    price_list = models.ForeignKey(PriceList, on_delete=models.PROTECT, related_name="gyms", help_text="Where its prices were copied from")
    branch_quota = models.PositiveSmallIntegerField(default=1, help_text="Branches it can have open at once")
    billing_day = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(LAST_BILLING_DAY)],
        help_text="Day of the month its invoice is written, for the month ahead",
    )
    whatsapp_mode = models.CharField(max_length=8, choices=WHATSAPP_MODES, default=SHARED)
    paid_until = models.DateField(null=True, blank=True, help_text="Last day its paid invoices cover")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(branch_quota__gte=1), name="billing_quota_at_least_one"),
            models.CheckConstraint(condition=models.Q(billing_day__gte=1, billing_day__lte=LAST_BILLING_DAY), name="billing_day_in_month"),
        ]

    def __str__(self):
        return f"Dumbelo plan of {self.gym}"

    @property
    def monthly_paise(self) -> int:
        return self.base_paise + self.per_branch_paise * self.branch_quota


class BranchRequest(TimeStamped):
    """A gym's admin asking for room for more branches. A Dumbelo admin approves (the quota goes up at once and
    the rest of the billing month is charged on the next invoice) or declines it. Never deleted."""

    ASKED, APPROVED, DECLINED = "asked", "approved", "declined"
    STATUS = [(ASKED, "Asked"), (APPROVED, "Approved"), (DECLINED, "Declined")]
    MAX = 5  # more than this at once is a conversation with Dumbelo, not a tap

    gym = models.ForeignKey("gyms.Gym", on_delete=models.CASCADE, related_name="branch_requests")
    count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(MAX)])
    note = models.CharField(max_length=200, blank=True, help_text="What the admin told Dumbelo, e.g. where it opens")
    asked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=10, choices=STATUS, default=ASKED)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    decided_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.CharField(max_length=200, blank=True)
    # Approving charges the rest of the billing month it falls in, as a pending line for the next invoice.
    charged_from = models.DateField(null=True, blank=True, help_text="The gym's day it was approved")
    charged_to = models.DateField(null=True, blank=True, help_text="Last day of that billing month")
    period_days = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Days in that billing month")
    rate_paise = models.PositiveIntegerField(null=True, blank=True, help_text="The per-branch fee it was worked out at")
    pro_rata_paise = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["gym"], condition=models.Q(status="asked"), name="one_open_branch_request"),
        ]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["gym", "created_at"])]

    def __str__(self):
        return f"{self.count} more for {self.gym} ({self.status})"

    @property
    def days_charged(self):
        return (self.charged_to - self.charged_from).days + 1 if self.charged_from and self.charged_to else None


# Invoices

PAY_WITHIN_DAYS = 7  # an invoice is written on the billing day and due a week later


def financial_year(day: date) -> str:
    """'2026-27' for any day from 1 Apr 2026 to 31 Mar 2027: invoice and receipt numbers start again each April."""
    starts = day.year if day.month >= 4 else day.year - 1
    return f"{starts}-{(starts + 1) % 100:02d}"


class NumberSeries(models.Model):
    """The last number taken in a series ("invoice 2026-27"). Locked while the next one is taken, so two invoices
    written at once can't share a number, and a voided one keeps its number for good."""

    name = models.CharField(max_length=24, unique=True)
    last = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name}: {self.last}"


class InvoiceQuerySet(models.QuerySet):
    def with_paid(self):
        """Each invoice's paid total (leaving out voided payments) in the same query, so lists never ask per row."""
        return self.annotate(paid_total=Coalesce(Sum("payments__amount_paise", filter=Q(payments__voided=False)), 0))


class Invoice(TimeStamped):
    """What a gym owes Dumbelo for one billing month, written on its billing day for the month ahead. Never
    deleted: a wrong one is voided with a reason. Tax fields are there and zero until Dumbelo charges GST, so
    turning it on later changes no old invoice."""

    OPEN, PAID, VOID = "open", "paid", "void"
    STATUS = [(OPEN, "Open"), (PAID, "Paid"), (VOID, "Void")]

    gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="dumbelo_invoices")
    number = models.CharField(max_length=24, unique=True, help_text="RL/2026-27/0001: one series per financial year")
    period_from = models.DateField(help_text="The billing day it was written for: the first day it covers")
    period_to = models.DateField(help_text="The day before the next billing day")
    issued_on = models.DateField()
    due_on = models.DateField()
    status = models.CharField(max_length=6, choices=STATUS, default=OPEN)
    subtotal_paise = models.PositiveIntegerField(default=0)
    tax_paise = models.PositiveIntegerField(default=0, help_text="GST: zero until Dumbelo charges it")
    total_paise = models.PositiveIntegerField(default=0)
    void_reason = models.CharField(max_length=200, blank=True)
    voided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    voided_at = models.DateTimeField(null=True, blank=True)

    objects = InvoiceQuerySet.as_manager()

    class Meta:
        ordering = ["-period_from", "-id"]
        constraints = [models.UniqueConstraint(fields=["gym", "period_from"], name="one_invoice_per_gym_period")]
        indexes = [models.Index(fields=["gym", "status"], name="invoice_gym_status")]

    def __str__(self):
        return self.number

    def paid_paise(self) -> int:
        if hasattr(self, "paid_total"):
            return self.paid_total
        return self.payments.filter(voided=False).aggregate(t=Sum("amount_paise"))["t"] or 0

    def owed_paise(self) -> int:
        return self.total_paise - self.paid_paise() if self.status == self.OPEN else 0


class InvoiceLine(TimeStamped):
    """One thing on an invoice. A line with no invoice yet is pending: a setup fee or charge a Dumbelo admin
    added, or the pro-rata cost of branches approved during the month. The next invoice picks them up."""

    BASE, BRANCHES, BRANCHES_PRO_RATA = "base", "branches", "branches_pro_rata"
    WHATSAPP_USAGE, WHATSAPP_SETUP, MACHINE_SETUP, ADJUSTMENT = "whatsapp_usage", "whatsapp_setup", "machine_setup", "adjustment"
    KINDS = [
        (BASE, "Base fee"), (BRANCHES, "Branches"), (BRANCHES_PRO_RATA, "Branches added during the month"),
        (WHATSAPP_USAGE, "WhatsApp messages"), (WHATSAPP_SETUP, "WhatsApp setup"), (MACHINE_SETUP, "Attendance machine setup"),
        (ADJUSTMENT, "Other charge"),
    ]
    CHARGES = (WHATSAPP_SETUP, MACHINE_SETUP, ADJUSTMENT)  # what a Dumbelo admin adds by hand (Add Charge)

    gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="+")
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.PROTECT, related_name="lines")
    kind = models.CharField(max_length=20, choices=KINDS)
    description = models.CharField(max_length=200)
    starts = models.DateField(null=True, blank=True, help_text="First day it covers, for charges by the month or the day")
    ends = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    rate_paise = models.PositiveIntegerField()
    amount_paise = models.PositiveIntegerField()
    tax_rate_bp = models.PositiveSmallIntegerField(default=0, help_text="GST in hundredths of a percent (1800 = 18%): zero for now")
    tax_paise = models.PositiveIntegerField(default=0)
    branch_request = models.OneToOneField(BranchRequest, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_line")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["gym", "invoice"], name="invoice_line_gym_invoice")]

    def __str__(self):
        return self.description


class InvoicePayment(TimeStamped):
    """Money a gym paid Dumbelo against one invoice, in full or in part. Recorded by a Dumbelo admin (no payment
    gateway). Never deleted: a wrong one is voided with a reason and keeps its receipt number."""

    METHODS = [("bank", "Bank transfer"), ("upi", "UPI"), ("cheque", "Cheque"), ("card", "Card"), ("cash", "Cash")]

    gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="+")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    receipt_number = models.CharField(max_length=24, unique=True, help_text="RLR/2026-27/0001: one series per financial year")
    amount_paise = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=METHODS)
    reference = models.CharField(max_length=80, blank=True, help_text="UTR, cheque or transaction number")
    paid_on = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    voided = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=200, blank=True)
    voided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    voided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-paid_on", "-id"]
        indexes = [models.Index(fields=["gym", "voided"], name="invoice_payment_gym")]

    def __str__(self):
        return self.receipt_number
