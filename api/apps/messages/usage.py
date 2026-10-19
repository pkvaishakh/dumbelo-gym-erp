"""What a gym's messages on Dumbelo's shared number cost it: delivered billable messages, counted from the rows.

Never a running counter. A message counts once, in the month Meta says it was delivered (`delivered_at`, read in
the gym's time zone), at the rate kept on it when it was sent. Meta repeating "delivered" sets nothing new, so it
can't count one twice; a message that never reached the phone costs nothing.
"""
from datetime import date

from django.db.models import Count, F, Q, Sum

from apps.core import clock
from apps.gyms.models import Gym

from .models import Message


def delivered(gym: Gym, first: date, last: date):
    """The gym's billable messages delivered from local day `first` to `last`, both included."""
    start, end = clock.day_bounds(gym, first)[0], clock.day_bounds(gym, last)[1]
    return Message.objects.filter(gym=gym, billable=True, delivered_at__gte=start, delivered_at__lt=end)


def usage(gym: Gym, first: date, last: date) -> list[dict]:
    """How many were delivered, by Meta's category and the rate kept on them: `category`, `rate_paise`,
    `messages` and `amount_paise`, cheapest first. One query."""
    rows = (delivered(gym, first, last).values(category=F("template__category"), rate=F("rate_paise"))
            .annotate(messages=Count("id")).order_by("rate", "category"))
    return [{"category": row["category"] or "", "rate_paise": row["rate"], "messages": row["messages"],
             "amount_paise": row["rate"] * row["messages"]} for row in rows]


def billed_in(first: date, last: date) -> Q:
    """Billable messages delivered from local day `first` to `last`, each day read in its gym's own time zone, as
    every gym's invoice counts them. One query for the time zones gyms are in."""
    days = Q(pk__in=[])
    for zone in Gym.objects.order_by().values_list("timezone", flat=True).distinct():
        where = Gym(timezone=zone)
        days |= Q(gym__timezone=zone, delivered_at__gte=clock.day_bounds(where, first)[0],
                  delivered_at__lt=clock.day_bounds(where, last)[1])
    return days & Q(billable=True)


def delivered_anywhere(first: date, last: date):
    """Every gym's billable messages delivered from local day `first` to `last` (see `billed_in`)."""
    return Message.objects.filter(billed_in(first, last))


def by_gym(messages):
    """Those messages per gym: `gym`, `gym_name`, `messages` and `amount_paise`, the biggest bill first."""
    return (messages.values("gym", gym_name=F("gym__name")).annotate(messages=Count("id"), amount_paise=Sum("rate_paise"))
            .order_by("-amount_paise", "gym_name", "gym"))
