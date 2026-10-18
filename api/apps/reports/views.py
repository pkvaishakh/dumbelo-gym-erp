from collections import Counter
from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.db.models.functions import TruncDate
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import CheckIn
from apps.attendance.services import count_by_session
from apps.core import clock
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, InGym
from apps.expenses.models import Expense
from apps.expenses.services import bills_due, sync_dues
from apps.payroll.services import salaries_owed
from apps.gyms.models import Branch
from apps.members.models import STATUSES, Member, Payment, Refund, Subscription
from apps.tasks.models import Task
from apps.tasks.services import overdue


class SummaryView(APIView):
    """The admin Home screen in one call: today's money, members by status, dues, and check-ins by session.
    For all branches it also gives each branch's day (`branches`), so the owner can compare them at a glance."""

    permission_classes = [InGym]
    roles = {"*": ADMIN + ("support",)}

    @extend_schema(parameters=[OpenApiParameter("date", str), OpenApiParameter("branch", int)], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        gym = request.gym
        day = clock.parse_date(request.query_params.get("date"), clock.today(gym))
        branch = int_param(request, "branch")
        start, end = clock.day_bounds(gym, day)
        month_start, _ = clock.day_bounds(gym, day.replace(day=1))

        pays = Payment.objects.filter(gym=gym, voided=False)
        refunds = Refund.objects.filter(gym=gym, voided=False)  # money given back: revenue less
        members = Member.objects.filter(gym=gym, is_archived=False).with_totals()
        checkins = CheckIn.objects.filter(gym=gym, local_date=day).select_related("branch", "staff", "gym").prefetch_related("branch__sessions")
        expenses = Expense.objects.filter(gym=gym, spent_on__gte=day.replace(day=1), spent_on__lte=day)
        if branch is not None:
            pays, members, checkins, expenses = pays.filter(branch_id=branch), members.filter(home_branch_id=branch), checkins.filter(branch_id=branch), expenses.filter(branch_id=branch)
            refunds = refunds.filter(branch_id=branch)

        statuses, dues_paise, dues_count = Counter(), 0, 0
        active_by_branch = Counter()
        for m in members:
            status = m.status(day)
            statuses[status] += 1
            if status in ("active", "expiring", "due"):
                active_by_branch[m.home_branch_id] += 1
            owed = m.balance_paise()
            if owed:
                dues_paise += owed
                dues_count += 1

        checkins = list(checkins)
        totals, sessions = count_by_session(checkins, gym)

        total = lambda qs: qs.aggregate(t=Sum("amount_paise"))["t"] or 0  # noqa: E731
        by_branch = lambda qs: dict(qs.values_list("branch_id").annotate(t=Sum("amount_paise")).order_by())  # noqa: E731
        revenue = by_branch(pays.filter(taken_at__gte=start, taken_at__lt=end))
        for b, t in by_branch(refunds.filter(refunded_at__gte=start, refunded_at__lt=end)).items():
            revenue[b] = revenue.get(b, 0) - t
        spent = by_branch(expenses.filter(spent_on=day))
        month = total(pays.filter(taken_at__gte=month_start, taken_at__lt=end)) - total(refunds.filter(refunded_at__gte=month_start, refunded_at__lt=end))
        body = {
            "date": day,
            "revenue": {"today_paise": sum(revenue.values()), "month_paise": month},
            "expenses_today_paise": sum(spent.values()),
            "expenses_month_paise": total(expenses),
            "members": {"total": sum(statuses.values()), **{s: statuses.get(s, 0) for s in STATUSES}},
            "dues": {"members": dues_count, "total_paise": dues_paise},
            "checkins": {"total": sum(totals.values()), "sessions": sessions},
            "expense_dues": self._expense_dues(gym, branch),
        }
        if branch is None:
            visits = Counter(c.branch_id for c in checkins)
            body["branches"] = [
                {"id": b.id, "name": b.name, "revenue_today_paise": revenue.get(b.id, 0), "expenses_today_paise": spent.get(b.id, 0),
                 "checkins": visits[b.id], "active_members": active_by_branch[b.id]}
                for b in Branch.objects.filter(gym=gym, is_active=True)
            ]
        return Response(body)

    @staticmethod
    def _expense_dues(gym, branch):
        """What the gym owes: bills inside their reminder days and approved salaries not paid in full. Always as of
        today, whatever day the summary shows, because a due is about now. The Dues screen shows the same figures."""
        today = clock.today(gym)
        sync_dues(gym, today)
        bills, salaries = bills_due(gym, today, branch), salaries_owed(gym, branch)
        return {"count": bills["count"] + salaries["count"], "overdue_bills": bills["overdue"], "bills": bills["count"],
                "salaries": salaries["count"], "total_paise": bills["total_paise"] + salaries["total_paise"]}


MAX_DAYS = 366


def _range(request, gym):
    """The report's first and last local day: the last 7 days unless the caller asks for others."""
    last = clock.parse_date(request.query_params.get("to"), clock.today(gym), field="to")
    first = clock.parse_date(request.query_params.get("from"), last - timedelta(days=6), field="from")
    if first > last:
        raise ValidationError({"from": ["Pick a start date on or before the end date"]})
    if (last - first).days >= MAX_DAYS:
        raise ValidationError({"from": ["Pick a range of a year or less"]})
    return first, last


class _Period:
    """The rows a report counts for one gym, optionally one branch, from `first` to `last` (local days)."""

    def __init__(self, gym, branch, first, last):
        lo, _ = clock.day_bounds(gym, first)
        _, hi = clock.day_bounds(gym, last)
        at = lambda field: {} if branch is None else {field: branch}  # noqa: E731
        self.payments = Payment.objects.filter(gym=gym, voided=False, taken_at__gte=lo, taken_at__lt=hi, **at("branch_id"))
        self.refunds = Refund.objects.filter(gym=gym, voided=False, refunded_at__gte=lo, refunded_at__lt=hi, **at("branch_id"))
        self.expenses = Expense.objects.filter(gym=gym, spent_on__range=(first, last), **at("branch_id"))
        self.joined = Member.objects.filter(gym=gym, is_archived=False, joined_on__range=(first, last), **at("home_branch_id"))
        self.checkins = CheckIn.objects.filter(gym=gym, member__isnull=False, local_date__range=(first, last), **at("branch_id"))
        # A task belongs to a branch through the person doing it.
        self.tasks = Task.objects.filter(gym=gym, due_date__range=(first, last), **at("assignee__branches"))
        # A renewal is a plan sold to a member who already had one.
        earlier = Subscription.objects.filter(member=OuterRef("member"), starts__lt=OuterRef("starts"))
        self.renewals = Subscription.objects.filter(
            member__gym=gym, cancelled=False, created_at__gte=lo, created_at__lt=hi, **at("member__home_branch_id"),
        ).filter(Exists(earlier))

    def refunded(self) -> int:
        return self.refunds.aggregate(t=Sum("amount_paise"))["t"] or 0

    def totals(self):
        return {
            # Revenue is what was taken less what was given back in the same days.
            "revenue_paise": (self.payments.aggregate(t=Sum("amount_paise"))["t"] or 0) - (refunded := self.refunded()),
            "refunds_paise": refunded,
            "new_members": self.joined.count(),
            "renewals": self.renewals.count(),
            "checkins": self.checkins.count(),
            "tasks_done": self.tasks.filter(status=Task.DONE).count(),
        }


class PeriodView(APIView):
    """The admin Reports screen for any range of days (`from`, `to`; the last 7 days by default): money in and out,
    new members, check-ins and tasks, each with the period of the same length just before it to compare."""

    permission_classes = [InGym]
    roles = {"*": ADMIN + ("support",)}

    @extend_schema(parameters=[OpenApiParameter("from", str), OpenApiParameter("to", str), OpenApiParameter("branch", int)], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        gym = request.gym
        first, last = _range(request, gym)
        branch = int_param(request, "branch")
        span = (last - first).days + 1
        now = _Period(gym, branch, first, last)
        before = _Period(gym, branch, first - timedelta(days=span), first - timedelta(days=1))

        totals = now.totals()
        totals["expenses_paise"] = now.expenses.aggregate(t=Sum("amount_paise"))["t"] or 0
        return Response({
            "from": first, "to": last, "days": span,
            "totals": totals,
            "previous": {"from": first - timedelta(days=span), "to": first - timedelta(days=1), **before.totals()},
            "series": self._series(gym, now, first, last),
            "revenue_by_plan": self._by_plan(now),
            "expenses_by_category": [
                {"category": c, "label": dict(Expense.CATEGORIES).get(c, c), "paise": t}
                for c, t in now.expenses.values_list("category").annotate(t=Sum("amount_paise")).order_by("-t")
            ],
            "tasks": self._tasks(gym, now.tasks),
        })

    @staticmethod
    def _by_plan(p):
        """Each plan's revenue, less what was refunded for it in the same days, largest first."""
        net = dict(p.payments.values_list("subscription__plan__name").annotate(t=Sum("amount_paise")).order_by())
        for name, t in p.refunds.values_list("subscription__plan__name").annotate(t=Sum("amount_paise")).order_by():
            net[name] = net.get(name, 0) - t
        return [{"name": name or "Other payments", "paise": t} for name, t in sorted(net.items(), key=lambda x: -x[1])]

    @staticmethod
    def _series(gym, p, first, last):
        """Each day's revenue, new members and check-ins, with the empty days filled in."""
        revenue = dict(p.payments.annotate(d=TruncDate("taken_at", tzinfo=clock.tz(gym))).values_list("d").annotate(t=Sum("amount_paise")).order_by())
        given = p.refunds.annotate(d=TruncDate("refunded_at", tzinfo=clock.tz(gym))).values_list("d").annotate(t=Sum("amount_paise")).order_by()
        for d, t in given:
            revenue[d] = revenue.get(d, 0) - t
        joined = dict(p.joined.values_list("joined_on").annotate(n=Count("id")).order_by())
        visits = dict(p.checkins.values_list("local_date").annotate(n=Count("id")).order_by())
        return [
            {"date": d, "revenue_paise": revenue.get(d, 0), "new_members": joined.get(d, 0), "checkins": visits.get(d, 0)}
            for d in clock.days_between(first, last)
        ]

    @staticmethod
    def _tasks(gym, tasks):
        """Tasks due in the period: where they stand, each person's share, and the oldest overdue ones to chase."""
        late = overdue(gym)
        counted = {
            "total": Count("id"), "todo": Count("id", filter=Q(status=Task.TODO)), "doing": Count("id", filter=Q(status=Task.DOING)),
            "done": Count("id", filter=Q(status=Task.DONE)), "overdue": Count("id", filter=late),
        }
        people = (
            tasks.values("assignee", "assignee__user__name", "assignee__role")
            .annotate(total=counted["total"], done=counted["done"], overdue=counted["overdue"])
            .order_by("-overdue", "-total", "assignee__user__name")
        )
        return {
            **tasks.aggregate(**counted),
            "people": [
                {"id": p["assignee"], "name": p["assignee__user__name"], "role": p["assignee__role"], "total": p["total"], "done": p["done"], "overdue": p["overdue"]}
                for p in people
            ],
            "late": [
                {"id": t.id, "title": t.title, "assignee_name": t.assignee.user.name, "due_date": t.due_date, "due_time": t.due_time}
                for t in tasks.filter(late).select_related("assignee__user").order_by("due_date", "due_time", "id")[:5]
            ],
        }
