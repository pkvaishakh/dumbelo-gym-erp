"""The scheduled side of reminders: work out who needs one, then send it. The rules live in services.py."""
from datetime import datetime

from celery import shared_task

from apps.reminders import services as reminders

from . import services


@shared_task
def send_reminders(at: str | None = None):
    """Give every gym whose own clock has just struck 6 its reminder list, and send the messages on it.

    This is the job beat runs (`CELERY_BEAT_SCHEDULE`). Both halves are safe to repeat, so the later ticks
    inside the same local hour find the list written and the messages sent and do nothing. `at` is an ISO
    timestamp, so a morning the worker missed can be run again by hand; beat passes nothing. Returns how
    many messages went out, for the worker's log.
    """
    now = datetime.fromisoformat(at) if at else None
    sent = 0
    for gym, day in reminders.gyms_at_reminder_hour(now):
        reminders.queue_for(gym, day)
        sent += services.send_due(gym, day)["sent"]
    return sent
