"""Console → Home: Dumbelo at a glance. The gyms by status, what they owe Dumbelo, branch requests waiting, demo requests not yet answered,
today's WhatsApp messages and the shared number's month, and whatever on the server is down or failed.

Counts and Dumbelo's own money only: never a member, a gym's payments or its check-ins. A fixed number of
queries whatever the number of gyms (the gyms are one aggregate over `gyms()`). Days and months are Dumbelo's,
India time, as on the Server screen and the WhatsApp log.
"""
from datetime import datetime

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.billing.invoicing import overdue_by_gym, overdue_invoices
from apps.billing.models import BranchRequest
from apps.core import clock
from apps.gyms.models import Gym
from apps.leads.models import Lead
from apps.messages.models import Message

from . import server
from .queries import gyms


def _gyms(today, month_starts: datetime) -> dict:
    """Gyms by status and new this month, and what they owe Dumbelo: one query."""
    def status(s):
        return Count("pk", filter=Q(status=s))

    t = gyms().annotate(late_paise=overdue_by_gym(today), late_invoices=overdue_invoices(today)).aggregate(
        active=status(Gym.ACTIVE), trial=status(Gym.TRIAL), suspended=status(Gym.SUSPENDED),
        new_this_month=Count("pk", filter=Q(created_at__gte=month_starts)),
        owed=Coalesce(Sum("owed_paise"), 0), owing=Count("pk", filter=Q(owed_paise__gt=0)),
        overdue=Coalesce(Sum("late_paise"), 0), overdue_count=Coalesce(Sum("late_invoices"), 0),
        overdue_gyms=Count("pk", filter=Q(late_paise__gt=0)),
    )
    return {
        "gyms": {k: t[k] for k in ("active", "trial", "suspended", "new_this_month")},
        "money": {"owed_paise": t["owed"], "gyms_owing": t["owing"], "overdue_paise": t["overdue"],
                  "overdue_invoices": t["overdue_count"], "gyms_overdue": t["overdue_gyms"]},
    }


def _whatsapp(now: datetime, today, month_starts: datetime) -> dict:
    """Delivered today on every number; the shared number's billable messages delivered this month and what they
    come to; failed today and waiting for a retry (the Server screen's counts). Three queries."""
    delivered = Message.objects.filter(delivered_at__gte=month_starts).aggregate(
        delivered_today=Count("pk", filter=Q(delivered_at__gte=clock.day_bounds(None, today)[0])),
        shared_messages=Count("pk", filter=Q(billable=True)),
        shared_paise=Coalesce(Sum("rate_paise", filter=Q(billable=True)), 0),
    )
    return {**delivered, **server.message_counts(now)}


def summary(now: datetime | None = None) -> dict:
    now = now or timezone.now()
    today = timezone.localdate(now)
    month_starts = clock.day_bounds(None, today.replace(day=1))[0]
    checks = server.health(now)
    return {
        "checked_at": now,
        **_gyms(today, month_starts),
        "branch_requests": {"waiting": BranchRequest.objects.filter(status=BranchRequest.ASKED).count()},
        "leads": {"new": Lead.objects.filter(status=Lead.NEW).count()},
        "whatsapp": _whatsapp(now, today, month_starts),
        "server": {
            "down": [c for c in checks if c.state == server.DOWN],
            "failed_jobs": server.failed_jobs(server.job_rows()),
        },
    }
