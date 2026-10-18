"""The days a report covers and the rows it counts in them. Every report reads its range here and builds only the
querysets it uses."""
from datetime import date, timedelta
from functools import cached_property

from django.db.models import Count, Exists, F, OuterRef, Q, Sum
from django.db.models.functions import TruncDate
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import CheckIn
from apps.core import clock
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, InGym
from apps.expenses.models import Expense
from apps.gyms.models import Branch
from apps.members.models import Member, Payment, Refund, Subscription
from apps.tasks.models import Task

#: The longest range a report covers, in calendar months: 19 Jul to 18 Oct, never 18 Jul. The web keeps the same
#: number in src/lib/reports.ts.
MAX_MONTHS = 3

#: The most rows a report lists (refunds, money moves, cash counts, bills); it gives the full count beside them.
LIST_MAX = 50

PARAMS = [
    OpenApiParameter("from", str, description="First local day, YYYY-MM-DD. 6 days before `to` when left out"),
    OpenApiParameter("to", str, description="Last local day, YYYY-MM-DD: the gym's today or earlier. Today when left out"),
    OpenApiParameter("branch", int, description="One branch; every branch when left out"),
]


def earliest(last: date) -> date:
    """The first day a range ending on `last` may start: the day after the same date 3 months before."""
    return clock.add_months(last, -MAX_MONTHS) + timedelta(days=1)


def report_range(request, gym) -> tuple[date, date]:
    """The report's first and last local day: the last 7 days unless the caller asks for others, at most 3 months,
    and never after the gym's today."""
    today = clock.today(gym)
    last = clock.parse_date(request.query_params.get("to"), today, field="to")
    first = clock.parse_date(request.query_params.get("from"), last - timedelta(days=6), field="from")
    if last > today:
        raise ValidationError({"to": ["Pick today or an earlier day"]})
    if first > last:
        raise ValidationError({"from": ["Pick a start date on or before the end date"]})
    if first < earliest(last):
        raise ValidationError({"from": [f"Pick a range of {MAX_MONTHS} months or less"]})
    return first, last


def net(taken: dict, given: dict) -> dict:
    """Money taken less money given back, key by key: revenue less refunds."""
    out = dict(taken)
    for k, t in given.items():
        out[k] = out.get(k, 0) - t
    return out


def summed(qs, key: str, total: str = "amount_paise") -> dict:
    """{key: sum of `total`} over `qs`."""
    return dict(qs.values_list(key).annotate(t=Sum(total)).order_by())


def counted(qs, key: str) -> dict:
    """{key: how many rows} over `qs`."""
    return dict(qs.values_list(key).annotate(n=Count("id")).order_by())


def ranked(totals: dict, label=str) -> list[dict]:
    """Breakdown rows for a BarList, largest first: {key, label, paise}. A missing key (no plan) keys as ""."""
    rows = [{"key": "" if k is None else str(k), "label": label(k), "paise": t} for k, t in totals.items()]
    return sorted(rows, key=lambda r: (-r["paise"], r["label"]))


def branch_names(gym) -> dict:
    return dict(Branch.objects.filter(gym=gym).values_list("id", "name"))


class Period:
    """The rows a report counts for one gym, optionally one branch, from `first` to `last` (local days)."""

    #: What dates each kind of row, so two spans can be compared in one query (`compare`) and counted by day (`daily`).
    DATED = {"payments": "taken_at", "refunds": "refunded_at", "expenses": "spent_on", "joined": "joined_on", "checkins": "local_date",
             "tasks": "due_date", "renewals": "created_at"}

    def __init__(self, gym, branch: int | None, first: date, last: date):
        self.gym, self.branch, self.first, self.last = gym, branch, first, last
        self.days = (last - first).days + 1
        self.lo, self.hi = clock.day_bounds(gym, first)[0], clock.day_bounds(gym, last)[1]

    def at(self, field: str) -> dict:
        """The branch filter on `field`, or none for every branch."""
        return {} if self.branch is None else {field: self.branch}

    @property
    def previous(self) -> "Period":
        """The same number of days just before, to compare against."""
        return Period(self.gym, self.branch, self.first - timedelta(days=self.days), self.first - timedelta(days=1))

    def head(self, trend: bool) -> dict:
        out = {"from": self.first, "to": self.last, "days": self.days}
        if trend:
            out["previous"] = {"from": self.previous.first, "to": self.previous.last}
        return out

    @cached_property
    def payments(self):
        return Payment.objects.filter(gym=self.gym, voided=False, taken_at__gte=self.lo, taken_at__lt=self.hi, **self.at("branch_id"))

    @cached_property
    def refunds(self):
        return Refund.objects.filter(gym=self.gym, voided=False, refunded_at__gte=self.lo, refunded_at__lt=self.hi, **self.at("branch_id"))

    @cached_property
    def expenses(self):
        return Expense.objects.filter(gym=self.gym, spent_on__range=(self.first, self.last), **self.at("branch_id"))

    @cached_property
    def joined(self):
        return Member.objects.filter(gym=self.gym, is_archived=False, joined_on__range=(self.first, self.last), **self.at("home_branch_id"))

    @cached_property
    def checkins(self):
        """Members' and staff's check-ins."""
        return CheckIn.objects.filter(gym=self.gym, local_date__range=(self.first, self.last), **self.at("branch_id"))

    @cached_property
    def tasks(self):
        # A task belongs to a branch through the person doing it.
        return Task.objects.filter(gym=self.gym, due_date__range=(self.first, self.last), **self.at("assignee__branches"))

    @cached_property
    def renewals(self):
        """Plans sold to a member who already had one."""
        earlier = Subscription.objects.filter(member=OuterRef("member"), starts__lt=OuterRef("starts"))
        return Subscription.objects.filter(
            member__gym=self.gym, cancelled=False, created_at__gte=self.lo, created_at__lt=self.hi, **self.at("member__home_branch_id"),
        ).filter(Exists(earlier))

    def _rows(self, name: str, only: Q | None):
        qs = getattr(self, name)
        return qs if only is None else qs.filter(only)

    def compare(self, name: str, total: str | None = None, only: Q | None = None) -> tuple[int, int]:
        """The sum of `total` (a count when None) over this period's `name` rows, and the same for the days just
        before it, in one query."""
        both = Period(self.gym, self.branch, self.previous.first, self.last)._rows(name, only)
        field = self.DATED[name]
        cut = self.lo if field.endswith("_at") else self.first
        measure = (lambda q: Sum(total, filter=q)) if total else (lambda q: Count("id", filter=q))  # noqa: E731
        r = both.aggregate(now=measure(Q(**{f"{field}__gte": cut})), before=measure(Q(**{f"{field}__lt": cut})))
        return r["now"] or 0, r["before"] or 0

    def daily(self, name: str, total: str | None = None, only: Q | None = None) -> dict:
        """{local day: sum of `total` (a count when None)} over this period's `name` rows. Days with none are missing."""
        field = self.DATED[name]
        day = TruncDate(field, tzinfo=clock.tz(self.gym)) if field.endswith("_at") else F(field)
        rows = self._rows(name, only).annotate(d=day).values_list("d").annotate(t=Sum(total) if total else Count("id")).order_by()
        return dict(rows)

    def every_day(self) -> list[date]:
        return clock.days_between(self.first, self.last)


class ReportView(APIView):
    """One report over the range and branch asked for. Admins only, and Rackline support inside its window."""

    permission_classes = [InGym]
    roles = {"*": ADMIN + ("support",)}
    #: Also name the days just before, which the screen compares against.
    trend = True

    def get(self, request):
        first, last = report_range(request, request.gym)
        p = Period(request.gym, int_param(request, "branch"), first, last)
        return Response({**p.head(self.trend), **self.report(p)})

    def report(self, p: Period) -> dict:
        raise NotImplementedError
