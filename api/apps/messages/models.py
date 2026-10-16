from django.db import models

from apps.core.models import GymScoped
from apps.reminders.models import ReminderDue


class Message(GymScoped):
    """One reminder that went to a member, or the record of one that didn't.

    A member hears from us at most once a day: that is what the unique constraint says, and it means a
    member whose plan is ending *and* who owes money gets the more pressing of the two, and a provider
    having a bad morning can't turn into a pile of retries. The text is kept as it was sent, so the desk
    can see exactly what the member read.
    """

    SENT, FAILED = "sent", "failed"
    STATUSES = [(SENT, "Sent"), (FAILED, "Failed")]

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="messages")
    kind = models.CharField(max_length=12, choices=ReminderDue.KINDS)
    to = models.CharField(max_length=13, help_text="The number it was sent to, as it was that day")
    text = models.TextField()
    for_date = models.DateField(help_text="The day in the gym's time zone this reminder was for")
    status = models.CharField(max_length=8, choices=STATUSES)
    provider = models.CharField(max_length=20, help_text="Which sender handled it (see senders.py)")
    provider_id = models.CharField(max_length=80, blank=True, help_text="The provider's own id for the message")
    error = models.CharField(max_length=200, blank=True, help_text="Why it failed, in the provider's words")

    class Meta:
        ordering = ["-for_date", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["gym", "member", "for_date"], name="one_message_per_member_per_day")]
        indexes = [models.Index(fields=["gym", "for_date"], name="message_gym_day")]

    def __str__(self):
        return f"{self.member} · {self.get_kind_display()} · {self.get_status_display()}"
