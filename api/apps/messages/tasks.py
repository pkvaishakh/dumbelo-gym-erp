"""The scheduled side of messages, and the messages queued when something happens. The rules live in services.py,
automation.py (when, and whether) and notify.py (receipts, tasks and Dumbelo's own)."""
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.jobs import run_job
from apps.core.models import JobRun
from apps.reminders import services as reminders

from . import notify, services
from .automation import reminder_runs
from .models import WebhookEvent
from .webhook import replay

#: How far back Run Now's webhook replay looks for calls that couldn't be handled.
REPLAY_DAYS = 7


def reminder_tick(now: datetime | None = None) -> dict[str, int]:
    """One tick of the reminders job: the lists and sends of the gyms whose hour it is, then the owners' invoice
    reminders. Says how many reminders were listed, sent, not sent and skipped, and how many owners were reminded."""
    counts = {"listed": 0, "sent": 0, "failed": 0, "skipped": 0, "owner_reminders": 0}
    for run in reminder_runs(now):
        counts["listed"] += reminders.queue_for(run.gym, run.day, run.days_ahead)
        if run.send:
            for k, n in services.send_due(run.gym, run.day, run.send).items():
                counts[k] += n
    counts["owner_reminders"] = notify.invoice_reminders(now)
    return counts


@shared_task
def send_reminders(at: str | None = None, run_id: int | None = None):
    """Give every gym whose own clock has reached one of its reminder hours its reminder list, send the reminders
    whose hour it is, and remind owners about their Dumbelo invoices.

    This is the job beat runs every quarter hour (`CELERY_BEAT_SCHEDULE`). The hours and days come from the
    database on every tick (`automation.py`), so a change applies on the next one. Everything here is safe to
    repeat, so the later ticks inside the same local hour find the list written and the messages sent and do
    nothing. `at` is an ISO timestamp, so a morning the worker missed can be run again by hand; beat passes
    nothing; Run Now passes the run it queued. Every run is kept (`apps.core.jobs`). Returns how many messages went
    out, for the worker's log.
    """
    now = datetime.fromisoformat(at) if at else None
    counts = run_job(JobRun.REMINDERS, lambda: reminder_tick(now), run_id=run_id, by_hand=at is not None)
    return counts.get("sent", 0) + counts.get("owner_reminders", 0)


@shared_task
def retry_messages(at: str | None = None):
    """Try again the messages Meta turned away for now (rate limits, Meta busy) whose wait is over.

    Beat runs it every minute. Each message is taken by one run only, so overlapping runs can't send one twice.
    `at` is an ISO timestamp for running it by hand; beat passes nothing. Returns how many went out.
    """
    now = datetime.fromisoformat(at) if at else None
    return run_job(JobRun.RETRIES, lambda: services.send_retries(now), by_hand=at is not None).get("sent", 0)


@shared_task
def replay_webhook_calls(run_id: int | None = None):
    """Handle again Meta's calls of the last REPLAY_DAYS that couldn't be handled: Run Now on the Console's Server
    screen, once the cause is fixed. Safe to repeat (`webhook.process`). `manage.py replay_webhook_events` picks
    other calls by time or id. Returns how many went through."""
    since = timezone.now() - timedelta(days=REPLAY_DAYS)
    events = WebhookEvent.objects.filter(created_at__gte=since).exclude(error="")
    return run_job(JobRun.WEBHOOK_REPLAY, lambda: replay(events), run_id=run_id).get("handled", 0)


@shared_task
def send_payment_receipt(payment_id: int, with_ids: list[int] | None = None):
    """The member's receipt, queued once the payment is saved (`notify.after_commit`). `with_ids`: the other parts of
    a split payment, so one receipt covers the total."""
    notify.payment_received(payment_id, with_ids or [])


@shared_task
def send_task_assigned(task_id: int):
    """The staff member's message about a task an admin gave them, queued once the task is saved."""
    notify.task_assigned(task_id)


@shared_task
def send_dumbelo_receipt(payment_id: int):
    """The owner's message that Dumbelo received their payment, queued once it is recorded."""
    notify.dumbelo_payment_received(payment_id)
