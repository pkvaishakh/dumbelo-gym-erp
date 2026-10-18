"""What a gym pays Rackline: the price list, each gym's Rackline plan and the branches it asks to add.

"Rackline plan" in code and copy, never just "plan": `members.Plan` is what a member buys from the gym.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStamped

# Invoices are written on the billing day, so it stops at 28: every month has one.
LAST_BILLING_DAY = 28


class Prices(models.Model):
    """Rackline's prices, all in paise. A price list holds them; each gym's plan keeps its own copy."""

    base_paise = models.PositiveIntegerField(help_text="Monthly base fee")
    per_branch_paise = models.PositiveIntegerField(help_text="Monthly fee for each branch the plan has room for")
    whatsapp_setup_paise = models.PositiveIntegerField(help_text="One time, for setting up WhatsApp")
    machine_setup_paise = models.PositiveIntegerField(help_text="One time, for each attendance machine")
    # A delivered message on Rackline's shared number, by Meta's category
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
    """Rackline's prices from a day on. Never changed once added: new prices are a new list. A new list never
    reprices a gym by itself; a Rackline admin moves each gym to it."""

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
        """The list in force on `on` (Rackline's today): the latest one that has started. None before the first."""
        return cls.objects.filter(active_from__lte=on or timezone.localdate()).order_by("-active_from").first()


class GymBilling(Prices, TimeStamped):
    """A gym's Rackline plan: its prices (copied from a price list), how many branches it pays for, its billing day
    and how it sends WhatsApp. The monthly charge is the base fee plus the per-branch fee times the quota."""

    SHARED, OWN, OFF = "shared", "own", "off"
    WHATSAPP_MODES = [(SHARED, "Rackline's number"), (OWN, "The gym's own number"), (OFF, "Off")]

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
        return f"Rackline plan of {self.gym}"

    @property
    def monthly_paise(self) -> int:
        return self.base_paise + self.per_branch_paise * self.branch_quota


class BranchRequest(TimeStamped):
    """A gym's admin asking for room for more branches. A Rackline admin approves (the quota goes up at once and
    the rest of the billing month is charged on the next invoice) or declines it. Never deleted."""

    ASKED, APPROVED, DECLINED = "asked", "approved", "declined"
    STATUS = [(ASKED, "Asked"), (APPROVED, "Approved"), (DECLINED, "Declined")]
    MAX = 5  # more than this at once is a conversation with Rackline, not a tap

    gym = models.ForeignKey("gyms.Gym", on_delete=models.CASCADE, related_name="branch_requests")
    count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(MAX)])
    note = models.CharField(max_length=200, blank=True, help_text="What the admin told Rackline, e.g. where it opens")
    asked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=10, choices=STATUS, default=ASKED)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    decided_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.CharField(max_length=200, blank=True)
    # Approving charges the rest of the billing month it falls in; session 11's invoice bills it.
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
