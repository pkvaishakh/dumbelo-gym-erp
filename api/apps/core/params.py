"""Reading query parameters. A bad value is the caller's mistake: answer 400 with the field, never a 500."""
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination


def int_param(request, name):
    """The query parameter as an int, or None when it's missing or empty."""
    value = request.query_params.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError({name: ["Use a whole number"]})


class Pages(LimitOffsetPagination):
    """50 rows by default, never more than 100: screens ask for the next page instead of one huge one."""

    default_limit = 50
    max_limit = 100
