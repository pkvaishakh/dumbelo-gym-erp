"""Writing a day's reminder list as a job of its own. The rules live in services.py."""
from datetime import datetime

from celery import shared_task

from . import services


@shared_task
def sweep_reminders(at: str | None = None):
    """Give every gym whose local clock has just struck 6 its reminder list for the day.

    Beat ticks every quarter hour in UTC because gyms keep their own time zones: the sweep asks each gym what
    time it is rather than scheduling a job per zone, and the ticks inside the same local hour find the rows
    already written and add nothing. `at` is an ISO timestamp, so a day can be rebuilt by hand. Beat runs
    `apps.messages.tasks.send_reminders`, which does this and then sends; this is the list on its own,
    for a morning that needs rewriting without sending anything. Returns how many reminders were new.
    """
    now = datetime.fromisoformat(at) if at else None
    return sum(services.queue_for(gym, day) for gym, day in services.gyms_at_reminder_hour(now))
