import secrets
from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStamped


class Gym(TimeStamped):
    """A paying customer (tenant). Everything else hangs off a gym."""

    TRIAL, ACTIVE, SUSPENDED = "trial", "active", "suspended"
    STATUS = [(TRIAL, "Trial"), (ACTIVE, "Active"), (SUSPENDED, "Suspended")]
    OPEN = (TRIAL, ACTIVE)  # the gyms whose people can use the app
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, help_text="Sent by the app as the X-Gym header")
    status = models.CharField(max_length=12, choices=STATUS, default=TRIAL, db_index=True)
    status_reason = models.CharField(max_length=200, blank=True, help_text="Why a Dumbelo admin last suspended or activated it")
    status_changed_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=40, default="Asia/Kolkata")
    month_days = models.PositiveSmallIntegerField(default=0, help_text="How long a plan's month runs: 0 for calendar months, else that many days (28, 30)")
    billing_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

    @property
    def is_suspended(self):
        return self.status == self.SUSPENDED


def _qr_code():
    return secrets.token_urlsafe(9)


class Branch(TimeStamped):
    DAYS = [("every_day", "Every day"), ("mon_sat", "Monday to Saturday")]
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=80)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    days_open = models.CharField(max_length=12, choices=DAYS, default="every_day")
    qr_code = models.CharField(max_length=24, unique=True, default=_qr_code, help_text="Printed on the wall QR: /checkin/<qr_code>")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["gym", "name"], name="branch_name_unique_in_gym")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.gym})"

    def session_for(self, at_time: time):
        """The session a check-in at this time belongs to: the one it falls in, or during a break the next one
        (staff arrive early). After the last session, the last one. None if the branch has no sessions."""
        sessions = list(self.sessions.all())
        for s in sessions:
            if at_time < s.ends:
                return s
        return sessions[-1] if sessions else None


class BranchSession(TimeStamped):
    """Opening hours as named sessions: Morning 5-10 AM, Afternoon 12-4 PM... A gap between two means closed."""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="sessions")
    name = models.CharField(max_length=40)
    starts = models.TimeField()
    ends = models.TimeField()

    class Meta:
        ordering = ["starts"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "name"], name="session_name_unique_in_branch"),
            models.CheckConstraint(condition=models.Q(ends__gt=models.F("starts")), name="session_ends_after_start"),
        ]

    def __str__(self):
        return f"{self.name} {self.starts:%H:%M}-{self.ends:%H:%M}"

    def clean(self):
        clash = BranchSession.objects.filter(branch=self.branch, starts__lt=self.ends, ends__gt=self.starts).exclude(pk=self.pk).first()
        if clash:
            raise ValidationError(f"{self.name} overlaps {clash.name}")


class GymRole(TimeStamped):
    """A person's place in one gym: one role, the branches they work at or use, and whether they own the account."""

    ADMIN, RECEPTIONIST, TRAINER, MEMBER = "admin", "receptionist", "trainer", "member"
    ROLES = [(ADMIN, "Admin"), (RECEPTIONIST, "Receptionist"), (TRAINER, "Trainer"), (MEMBER, "Member")]
    STAFF_ROLES = (ADMIN, RECEPTIONIST, TRAINER)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gym_roles")
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=12, choices=ROLES)
    branches = models.ManyToManyField(Branch, blank=True, related_name="people", help_text="Ignored for admins: they see every branch")
    is_owner = models.BooleanField(default=False, help_text="The admin who handles Dumbelo billing; other admins can't remove them")
    is_active = models.BooleanField(default=True)
    # staff details shown on the staff profile
    shift = models.CharField(max_length=60, blank=True)
    specialities = models.CharField(max_length=120, blank=True)
    day_off = models.CharField(max_length=12, blank=True)
    device_user_id = models.CharField(max_length=20, blank=True, help_text="This person's number on the turnstile")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "gym"], name="one_role_per_gym"),
            models.UniqueConstraint(fields=["gym"], condition=models.Q(is_owner=True), name="one_owner_per_gym"),
        ]

    def __str__(self):
        return f"{self.user} · {self.get_role_display()} · {self.gym}"

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    def branch_ids(self):
        """None means every branch (admins); otherwise the ids this person may see."""
        if self.is_admin:
            return None
        return list(self.branches.values_list("id", flat=True))


class SupportAccess(TimeStamped):
    """Dumbelo's team may open a gym only inside a window an admin granted. Every view is audited."""

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="support_windows")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    starts = models.DateTimeField(default=timezone.now)
    ends = models.DateTimeField()

    class Meta:
        ordering = ["-starts"]

    @classmethod
    def open_for(cls, gym):
        now = timezone.now()
        return cls.objects.filter(gym=gym, starts__lte=now, ends__gt=now).exists()
