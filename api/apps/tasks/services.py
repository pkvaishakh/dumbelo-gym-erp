from django.db.models import Q

from apps.core import clock

from .models import Task


def overdue(gym) -> Q:
    """Not done, and the due day has passed, or it's today and the due time has passed (in the gym's clock)."""
    now = clock.local(gym)
    late = Q(due_date__lt=now.date()) | Q(due_date=now.date(), due_time__isnull=False, due_time__lt=now.time())
    return ~Q(status=Task.DONE) & late
