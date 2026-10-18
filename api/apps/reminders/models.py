from django.db import models

from apps.core.models import GymScoped


class ReminderDue(GymScoped):
    """One nudge a member has earned on one local day: their plan is ending, or they owe money.

    The daily job writes these; sending them is a separate step. The unique constraint is what makes the job
    safe to run twice: the second run finds the row already there and adds nothing. The kinds are the messages'
    own (`WhatsAppTemplate.KINDS`), so a reminder, its switch and its template share one name.
    """

    PLAN_ENDING, PLAN_ENDS_TODAY, PAYMENT_DUE = "plan_ending", "plan_ends_today", "payment_due"
    KINDS = [(PLAN_ENDING, "Plan ending soon"), (PLAN_ENDS_TODAY, "Plan ends today"), (PAYMENT_DUE, "Payment due")]
    #: How many days before a plan ends its members are warned, until Rackline sets other days (AutomationSchedule)
    DAYS_AHEAD = (7, 3)

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="reminders")
    kind = models.CharField(max_length=20, choices=KINDS)
    for_date = models.DateField(help_text="The day in the gym's time zone this reminder is for")
    days_left = models.PositiveSmallIntegerField(null=True, blank=True, help_text="For a plan ending soon: how many days it had left")

    class Meta:
        ordering = ["-for_date", "member__name"]
        constraints = [models.UniqueConstraint(fields=["gym", "member", "kind", "for_date"], name="one_reminder_per_member_kind_day")]
        indexes = [models.Index(fields=["gym", "for_date"], name="reminder_gym_day")]

    def __str__(self):
        return f"{self.member} · {self.get_kind_display()} · {self.for_date}"
