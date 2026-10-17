from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import IntegerField, OuterRef, Prefetch, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.core.models import GymScoped, TimeStamped

EXPIRING_DAYS = 7
STATUSES = ("active", "expiring", "due", "frozen", "expired", "none")  # what Member.status() can answer


class Plan(GymScoped):
    MEMBERSHIP, PT = "membership", "pt"
    KINDS = [(MEMBERSHIP, "Membership"), (PT, "Personal training")]
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=12, choices=KINDS, default=MEMBERSHIP)
    months = models.PositiveSmallIntegerField(default=0, help_text="Memberships: 1, 3, 6, 12")
    sessions = models.PositiveSmallIntegerField(default=0, help_text="Personal training: number of sessions")
    price_paise = models.PositiveIntegerField()
    includes = models.CharField(max_length=120, blank=True)
    on_sale = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["gym", "name"], name="plan_name_unique_in_gym")]
        ordering = ["kind", "price_paise"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.kind == self.MEMBERSHIP and not self.months:
            raise ValidationError({"months": "A membership plan needs a length"})
        if self.kind == self.PT and not self.sessions:
            raise ValidationError({"sessions": "A personal training plan needs a number of sessions"})


class Offer(GymScoped):
    """The only way to discount. The admin creates it; the desk picks one at sale."""

    name = models.CharField(max_length=80)
    percent_off = models.PositiveSmallIntegerField(null=True, blank=True)
    amount_off_paise = models.PositiveIntegerField(null=True, blank=True)
    plans = models.ManyToManyField(Plan, blank=True, help_text="Empty means every plan")
    starts = models.DateField()
    ends = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(percent_off__isnull=False, amount_off_paise__isnull=True) | models.Q(percent_off__isnull=True, amount_off_paise__isnull=False)),
                name="offer_percent_xor_amount",
            ),
            models.CheckConstraint(condition=models.Q(percent_off__lte=100), name="offer_percent_max_100"),
        ]

    def __str__(self):
        return self.name

    def applies_to(self, plan, on: date):
        if not self.is_active or not (self.starts <= on <= self.ends):
            return False
        return not self.plans.exists() or self.plans.filter(pk=plan.pk).exists()

    def discount_on(self, price_paise: int) -> int:
        if self.percent_off is not None:
            return price_paise * self.percent_off // 100
        return min(self.amount_off_paise or 0, price_paise)


def _total(qs, per, field):
    """A correlated SUM of `field` for each `per` row, for annotate(): 0 when there are no rows."""
    summed = qs.values(per).annotate(t=Sum(field)).values("t")
    return Coalesce(Subquery(summed, output_field=IntegerField()), Value(0))


class MemberQuerySet(models.QuerySet):
    def with_totals(self):
        """Everything status, balance and current plan need, for any number of members in two extra queries.

        Lists, the status filter and the Home summary use this; the methods below fall back to their own queries
        for a single member loaded without it."""
        owed = _total(Subscription.objects.filter(member=OuterRef("pk"), cancelled=False), "member", "price_paise")
        paid = _total(Payment.objects.filter(member=OuterRef("pk"), voided=False), "member", "amount_paise")
        live = Subscription.objects.filter(cancelled=False).select_related("plan").order_by("-ends")
        return self.annotate(owed_total=owed, paid_total=paid).prefetch_related(Prefetch("subscriptions", queryset=live, to_attr="live_subs"))


class Member(GymScoped):
    """The gym's view of a member. `user` is set when the desk creates their login (phone + password)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="member_profiles")
    code = models.CharField(max_length=20, help_text="Member ID shown on cards, e.g. RL-2041")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=13)
    email = models.EmailField(blank=True)
    home_branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="members")
    trainer = models.ForeignKey("gyms.GymRole", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_members")
    goal = models.CharField(max_length=60, blank=True)
    joined_on = models.DateField(default=date.today)
    device_user_id = models.CharField(max_length=20, blank=True, help_text="This member's number on the turnstile")
    reminders_opted_out = models.BooleanField(default=False, help_text="This member asked not to be sent reminders")
    is_archived = models.BooleanField(default=False)

    objects = MemberQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["gym", "code"], name="member_code_unique_in_gym"),
            models.UniqueConstraint(fields=["gym", "phone"], name="member_phone_unique_in_gym"),
        ]
        ordering = ["name"]
        indexes = [models.Index(fields=["gym", "joined_on"], name="member_gym_joined")]

    def __str__(self):
        return f"{self.name} ({self.code})"

    # ---- what the screens show, from the member's subscriptions and payments ----
    def _live_subs(self):
        """Subscriptions that aren't cancelled, latest end first: from with_totals() when loaded with it."""
        cached = getattr(self, "live_subs", None)
        return cached if cached is not None else list(self.subscriptions.filter(cancelled=False).select_related("plan").order_by("-ends"))

    def current_subscription(self, today=None):
        today = today or timezone.localdate()
        subs = self._live_subs()
        return next((s for s in subs if s.starts <= today), subs[0] if subs else None)

    def status(self, today=None):
        """active | expiring | due | frozen | expired | none — the same five badges the prototype shows."""
        today = today or timezone.localdate()
        sub = self.current_subscription(today)
        if sub is None:
            return "none"
        if sub.is_frozen(today):
            return "frozen"
        if sub.ends < today:
            return "expired"
        if self.balance_paise() > 0:
            return "due"
        if sub.ends <= today + timedelta(days=EXPIRING_DAYS):
            return "expiring"
        return "active"

    def balance_paise(self):
        """What the member still owes across subscriptions that aren't cancelled."""
        if hasattr(self, "owed_total"):
            return max(0, self.owed_total - self.paid_total)
        owed = self.subscriptions.filter(cancelled=False).aggregate(t=Sum("price_paise"))["t"] or 0
        paid = Payment.objects.filter(member=self, voided=False).aggregate(t=Sum("amount_paise"))["t"] or 0
        return max(0, owed - paid)


class MemberNote(TimeStamped):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    text = models.TextField()

    class Meta:
        ordering = ["-created_at"]


class SubscriptionQuerySet(models.QuerySet):
    def with_paid(self):
        """What has been paid toward each subscription, so a list doesn't sum payments row by row."""
        return self.annotate(paid_total=_total(Payment.objects.filter(subscription=OuterRef("pk"), voided=False), "subscription", "amount_paise"))


class Subscription(TimeStamped):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    starts = models.DateField()
    ends = models.DateField()
    list_price_paise = models.PositiveIntegerField(help_text="The plan's price at sale")
    offer = models.ForeignKey(Offer, null=True, blank=True, on_delete=models.PROTECT, related_name="subscriptions")
    price_paise = models.PositiveIntegerField(help_text="What the member owes for it, after the offer")
    frozen_from = models.DateField(null=True, blank=True)
    frozen_until = models.DateField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)
    sold_by = models.ForeignKey("gyms.GymRole", null=True, on_delete=models.SET_NULL, related_name="+")

    objects = SubscriptionQuerySet.as_manager()

    class Meta:
        ordering = ["-starts"]
        constraints = [models.CheckConstraint(condition=models.Q(ends__gte=models.F("starts")), name="subscription_ends_after_start")]

    def is_frozen(self, today=None):
        today = today or timezone.localdate()
        return bool(self.frozen_from and self.frozen_from <= today and (self.frozen_until is None or today <= self.frozen_until))

    def paid_paise(self):
        if hasattr(self, "paid_total"):  # annotated by the subscription list
            return self.paid_total
        return self.payments.filter(voided=False).aggregate(t=Sum("amount_paise"))["t"] or 0


class Payment(GymScoped):
    """Recorded at the desk (no gateway in the MVP). Admins may correct or void one; both are audited, never deleted."""

    METHODS = [("cash", "Cash"), ("upi", "UPI"), ("card", "Card"), ("bank", "Bank transfer")]
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="payments")
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.PROTECT, related_name="payments")
    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="payments")
    amount_paise = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=METHODS)
    taken_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    taken_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=200, blank=True)
    voided = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-taken_at"]
        constraints = [models.CheckConstraint(condition=models.Q(amount_paise__gt=0), name="payment_positive")]
