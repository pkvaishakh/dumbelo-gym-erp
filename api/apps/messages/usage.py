"""What a gym's messages on Rackline's shared number cost it: delivered billable messages, counted from the rows.

Never a running counter. A message counts once, in the month Meta says it was delivered (`delivered_at`, read in
the gym's time zone), at the rate kept on it when it was sent. Meta repeating "delivered" sets nothing new, so it
can't count one twice; a message that never reached the phone costs nothing.
"""
from datetime import date

from django.db.models import Count, F

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
