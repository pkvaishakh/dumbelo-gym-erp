import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import GymScoped, TimeStamped


class CheckIn(GymScoped):
    """Who came in, where and when. That's all the gym records: no check-out, no time spent inside.

    Exactly one of `member` or `staff` is set. Desk, wall QR and turnstile all write this same row.
    """

    DESK, QR, DEVICE = "desk", "qr", "device"
    SOURCES = [(DESK, "Front desk"), (QR, "Wall QR"), (DEVICE, "Turnstile or biometric")]

    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="checkins")
    member = models.ForeignKey("members.Member", null=True, blank=True, on_delete=models.CASCADE, related_name="checkins")
    staff = models.ForeignKey("gyms.GymRole", null=True, blank=True, on_delete=models.CASCADE, related_name="checkins")
    at = models.DateTimeField(default=timezone.now, db_index=True)
    local_date = models.DateField(db_index=True, help_text="The day in the gym's time zone; one check-in per person per day")
    source = models.CharField(max_length=8, choices=SOURCES)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-at"]
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(member__isnull=False, staff__isnull=True) | models.Q(member__isnull=True, staff__isnull=False)),
                name="checkin_member_xor_staff",
            ),
            models.UniqueConstraint(fields=["member", "local_date"], condition=models.Q(member__isnull=False), name="one_member_checkin_per_day"),
            models.UniqueConstraint(fields=["staff", "local_date"], condition=models.Q(staff__isnull=False), name="one_staff_checkin_per_day"),
        ]


def _token():
    return secrets.token_urlsafe(24)


class Device(TimeStamped):
    """A turnstile or biometric reader that pushes each punch to /api/devices/punch/ with its token."""

    branch = models.ForeignKey("gyms.Branch", on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=60)
    serial = models.CharField(max_length=60, unique=True)
    token = models.CharField(max_length=64, unique=True, default=_token)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.serial})"
