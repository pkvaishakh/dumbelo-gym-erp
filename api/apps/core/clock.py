"""Time in the gym's own time zone. Stored times are UTC; days, sessions and reports follow the gym's clock."""
import calendar
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone


def tz(gym):
    return ZoneInfo(getattr(gym, "timezone", None) or "Asia/Kolkata")


def local(gym, at=None):
    return timezone.localtime(at or timezone.now(), tz(gym))


def time_label(gym, at):
    """'6:05 AM' in the gym's time zone. Built by hand: strftime's no-padding flags differ between Linux and Windows."""
    return clock_label(local(gym, at))


def clock_label(t) -> str:
    """'6:05 AM' for a time of day already in the gym's time zone (a task's due time, a local datetime)."""
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def date_label(day: date) -> str:
    """'5 Oct' — a day in the words a member reads. Built by hand: %-d is Linux-only, %#d is Windows-only."""
    return f"{day.day} {day:%b}"


def today(gym):
    return local(gym).date()


def moment(value: str) -> datetime:
    """A time typed on the command line: ISO, or a day (its midnight). Without a time zone it is UTC, as everything
    stored is. Raises ValueError for anything else."""
    at = datetime.fromisoformat(value)
    return at if timezone.is_aware(at) else at.replace(tzinfo=UTC)


def day_bounds(gym, day: date):
    """UTC-aware start and end of a local day, for filtering `at` / `taken_at`."""
    start = datetime.combine(day, datetime.min.time(), tzinfo=tz(gym))
    return start, start + timedelta(days=1)


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def plan_end(starts: date, months: int) -> date:
    """A 1-month plan from 14 Oct runs to 13 Nov."""
    return add_months(starts, months or 3) - timedelta(days=1)


def parse_date(value, default, field="date"):
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({field: ["Use YYYY-MM-DD"]})


def days_between(first: date, last: date) -> list[date]:
    """Every day from first to last, both included."""
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]
