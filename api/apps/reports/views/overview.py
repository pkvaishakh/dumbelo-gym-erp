from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.tasks.models import Task

from ..period import PARAMS, Period, ReportView
from ..serializers import Overview
from .money import accounts_for


def _headline(now: int, before: int) -> dict:
    return {"value": now, "before": before}


@extend_schema(parameters=PARAMS, responses=Overview)
class OverviewView(ReportView):
    """One headline for each report, with the same figure for the days just before it: the Reports list, in a fixed
    handful of queries. Each figure is the one its report leads with, so the two always agree."""

    def report(self, p: Period) -> dict:
        taken, given = p.compare("payments", "amount_paise"), p.compare("refunds", "amount_paise")
        balances = list(accounts_for(p).values_list("opening_paise", "closing_paise"))
        done, done_before = p.compare("tasks", only=Q(status=Task.DONE))
        return {
            "revenue": _headline(taken[0] - given[0], taken[1] - given[1]),
            "expenses": _headline(*p.compare("expenses", "amount_paise")),
            "money": _headline(sum(c for _, c in balances), sum(o for o, _ in balances)),
            "members": _headline(*p.compare("joined")),
            "attendance": _headline(*p.compare("checkins", only=Q(member__isnull=False))),
            "tasks": {"value": done, "before": done_before, "total": p.tasks.count()},
        }
