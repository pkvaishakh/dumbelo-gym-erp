"""Writing a day's reminder list as a job of its own. The rules live in services.py."""
from datetime import datetime

from celery import shared_task

from apps.messages.automation import reminder_runs  # the times are Rackline's, kept with the messages

from . import services


@shared_task
def sweep_reminders(at: str | None = None):
    """Give every gym whose local clock has just reached one of its reminder hours its reminder list for the day.

    Beat runs `apps.messages.tasks.send_reminders`, which does this and then sends; this is the list on its own,
    for a morning that needs rewriting without sending anything. `at` is an ISO timestamp, so a day can be rebuilt
    by hand. Returns how many reminders were new.
    """
    now = datetime.fromisoformat(at) if at else None
    return sum(services.queue_for(run.gym, run.day, run.days_ahead) for run in reminder_runs(now))
