"""Reading query parameters. A bad value is the caller's mistake: answer 400 with the field, never a 500."""
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from . import clock
from .errors import RuleBroken


def int_param(request, name):
    """The query parameter as an int, or None when it's missing or empty."""
    value = request.query_params.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError({name: ["Use a whole number"]})


def day_range(request, today, *, many_days: bool, what: str):
    """The first and last local day asked for: ?date= for one day, or ?from=&to= (either end may be left out, and
    stands for the other end, or today). None when no day is asked for. The desk sees one day's money at a time, so
    without `many_days` a longer span is refused, saying `what` it was ("collection")."""
    p = request.query_params
    if day := clock.parse_date(p.get("date"), None):
        return day, day
    first = clock.parse_date(p.get("from"), None, field="from")
    last = clock.parse_date(p.get("to"), None, field="to")
    if not first and not last:
        return None
    first, last = first or last or today, last or today
    if first > last:
        raise ValidationError({"from": ["Pick a start date on or before the end date"]})
    if first != last and not many_days:
        raise RuleBroken("not_allowed", f"You can see one day's {what} at a time")
    return first, last


def open_days(request):
    """?from= and ?to=, either of which may be left out (None): for a log, where no end means no limit."""
    p = request.query_params
    first = clock.parse_date(p.get("from"), None, field="from")
    last = clock.parse_date(p.get("to"), None, field="to")
    if first and last and first > last:
        raise ValidationError({"from": ["Pick a start date on or before the end date"]})
    return first, last


class Pages(LimitOffsetPagination):
    """50 rows by default, never more than 100: screens ask for the next page instead of one huge one."""

    default_limit = 50
    max_limit = 100
