from collections import Counter

from django.db.models import Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from apps.members.models import STATUSES, Member, Payment, Refund


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

