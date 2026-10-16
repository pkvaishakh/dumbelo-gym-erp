"""The scheduled side of reminders. Beat runs the sweep every hour; the rules live in services.py."""
from datetime import datetime

from celery import shared_task

from . import services


@shared_task
def sweep_reminders(at: str | None = None):
    """Give every gym whose local clock has just struck 6 its reminder list for the day.

    Beat ticks every quarter hour in UTC because gyms keep their own time zones: the sweep asks each gym what
    time it is rather than scheduling a job per zone, and the ticks inside the same local hour find the rows
    already written and add nothing. `at` is an ISO timestamp, so a sweep the worker missed can be run again
    by hand; beat passes nothing. Returns how many reminders were new, for the worker's log.
    """
    now = datetime.fromisoformat(at) if at else None
    return sum(services.queue_for(gym, day) for gym, day in services.gyms_at_reminder_hour(now))
