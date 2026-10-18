"""The scheduled side of messages, and the messages queued when something happens. The rules live in services.py,
automation.py (when, and whether) and notify.py (receipts, tasks and Rackline's own)."""
from datetime import datetime

from celery import shared_task

from apps.reminders import services as reminders

from . import notify, services
from .automation import reminder_runs


@shared_task
def send_reminders(at: str | None = None):
    """Give every gym whose own clock has reached one of its reminder hours its reminder list, send the reminders
    whose hour it is, and remind owners about their Rackline invoices.

    This is the job beat runs every quarter hour (`CELERY_BEAT_SCHEDULE`). The hours and days come from the
    database on every tick (`automation.py`), so a change applies on the next one. Everything here is safe to
    repeat, so the later ticks inside the same local hour find the list written and the messages sent and do
    nothing. `at` is an ISO timestamp, so a morning the worker missed can be run again by hand; beat passes
    nothing. Returns how many messages went out, for the worker's log.
    """
    now = datetime.fromisoformat(at) if at else None
    sent = 0
    for run in reminder_runs(now):
        reminders.queue_for(run.gym, run.day, run.days_ahead)
        if run.send:
            sent += services.send_due(run.gym, run.day, run.send)["sent"]
    return sent + notify.invoice_reminders(now)


@shared_task
def retry_messages(at: str | None = None):
    """Try again the messages Meta turned away for now (rate limits, Meta busy) whose wait is over.

    Beat runs it every minute. Each message is taken by one run only, so overlapping runs can't send one twice.
    `at` is an ISO timestamp for running it by hand; beat passes nothing. Returns how many went out.
    """
    return services.send_retries(datetime.fromisoformat(at) if at else None)["sent"]


@shared_task
def send_payment_receipt(payment_id: int):
    """The member's receipt, queued once the payment is saved (`notify.after_commit`)."""
    notify.payment_received(payment_id)


@shared_task
def send_task_assigned(task_id: int):
    """The staff member's message about a task an admin gave them, queued once the task is saved."""
    notify.task_assigned(task_id)


@shared_task
def send_rackline_receipt(payment_id: int):
    """The owner's message that Rackline received their payment, queued once it is recorded."""
    notify.rackline_payment_received(payment_id)
