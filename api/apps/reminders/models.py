from django.db import models

from apps.core.models import GymScoped


class ReminderDue(GymScoped):
    """One nudge a member has earned on one local day: their plan is ending, or they owe money.

    The daily job writes these; sending them is a separate step. The unique constraint is what makes the job
    safe to run twice: the second run finds the row already there and adds nothing.
    """

    EXPIRING_7, EXPIRING_3, EXPIRING_0, DUES = "expiring_7", "expiring_3", "expiring_0", "dues"
    KINDS = [
        (EXPIRING_7, "Plan ends in 7 days"),
        (EXPIRING_3, "Plan ends in 3 days"),
        (EXPIRING_0, "Plan ends today"),
        (DUES, "Payment due"),
    ]
    #: how many days are left when each expiry reminder goes out
    DAYS_LEFT = {7: EXPIRING_7, 3: EXPIRING_3, 0: EXPIRING_0}

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="reminders")
    kind = models.CharField(max_length=12, choices=KINDS)
    for_date = models.DateField(help_text="The day in the gym's time zone this reminder is for")

    class Meta:
        ordering = ["-for_date", "member__name"]
        constraints = [models.UniqueConstraint(fields=["gym", "member", "kind", "for_date"], name="one_reminder_per_member_kind_day")]
        indexes = [models.Index(fields=["gym", "for_date"], name="reminder_gym_day")]

    def __str__(self):
        return f"{self.member} · {self.get_kind_display()} · {self.for_date}"
