from django.conf import settings
from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GymScoped(TimeStamped):
    """Every row that belongs to a gym carries the gym. All queries inside a gym filter on it (see core.tenancy)."""

    gym = models.ForeignKey("gyms.Gym", on_delete=models.CASCADE, related_name="+", db_index=True)

    class Meta:
        abstract = True


class JobRun(models.Model):
    """One run of a scheduled job: who started it (beat, Run Now in the Console, or someone by hand), when it started
    and finished, what it did as counts, and the error if it broke. Written by `apps.core.jobs.run_job`.

    A run that did nothing (`idle`) is kept only while it is its job's latest; the rest for 30 days. Run Now writes
    the row before the worker takes it (`started_at` empty until then), so the Console sees it waiting."""

    REMINDERS, INVOICES, RETRIES, WEBHOOK_REPLAY = "reminders", "invoices", "retries", "webhook_replay"
    JOBS = [(REMINDERS, "Reminders"), (INVOICES, "Rackline invoices"), (RETRIES, "Message retries"), (WEBHOOK_REPLAY, "Webhook replay")]
    BEAT, RUN_NOW, BY_HAND = "beat", "run_now", "by_hand"
    TRIGGERS = [(BEAT, "On schedule"), (RUN_NOW, "Run Now"), (BY_HAND, "By hand")]

    job = models.CharField(max_length=20, choices=JOBS)
    trigger = models.CharField(max_length=10, choices=TRIGGERS, default=BEAT)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                           help_text="Who pressed Run Now")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When it was started or queued")
    started_at = models.DateTimeField(null=True, blank=True, help_text="When the worker began it")
    finished_at = models.DateTimeField(null=True, blank=True)
    counts = models.JSONField(default=dict, help_text="What it did: how many sent, written, handled…")
    idle = models.BooleanField(default=False, help_text="Finished without an error and found nothing to do")
    error = models.CharField(max_length=200, blank=True, help_text="Why it stopped, if it broke")

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # Run Now is refused while the job runs; this also stops two presses at the same moment queueing it twice.
            models.UniqueConstraint(fields=["job"], condition=models.Q(trigger="run_now", finished_at__isnull=True),
                                    name="one_run_now_at_a_time"),
        ]
        indexes = [
            models.Index(fields=["job", "-created_at"], name="jobrun_job_latest"),
            models.Index(fields=["trigger", "started_at"], name="jobrun_beat_tick"),
        ]

    def __str__(self):
        return f"{self.get_job_display()} · {self.created_at:%Y-%m-%d %H:%M}"
