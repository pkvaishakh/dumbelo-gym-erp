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
from apps.members.models import STATUSES, Member, Payment


class SummaryView(APIView):
    """The admin Home screen in one call: today's money, members by status, dues, and check-ins by session."""

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
        members = Member.objects.filter(gym=gym, is_archived=False).with_totals()
        checkins = CheckIn.objects.filter(gym=gym, local_date=day).select_related("branch", "staff", "gym").prefetch_related("branch__sessions")
        expenses = Expense.objects.filter(gym=gym, spent_on__gte=day.replace(day=1), spent_on__lte=day)
        if branch is not None:
            pays, members, checkins, expenses = pays.filter(branch_id=branch), members.filter(home_branch_id=branch), checkins.filter(branch_id=branch), expenses.filter(branch_id=branch)

        statuses, dues_paise, dues_count = Counter(), 0, 0
        for m in members:
            statuses[m.status(day)] += 1
            owed = m.balance_paise()
            if owed:
                dues_paise += owed
                dues_count += 1

        totals, sessions = count_by_session(checkins, gym)

        total = lambda qs: qs.aggregate(t=Sum("amount_paise"))["t"] or 0  # noqa: E731
        return Response({
            "date": day,
            "revenue": {"today_paise": total(pays.filter(taken_at__gte=start, taken_at__lt=end)), "month_paise": total(pays.filter(taken_at__gte=month_start, taken_at__lt=end))},
            "expenses_month_paise": total(expenses),
            "members": {"total": sum(statuses.values()), **{s: statuses.get(s, 0) for s in STATUSES}},
            "dues": {"members": dues_count, "total_paise": dues_paise},
            "checkins": {"total": sum(totals.values()), "sessions": sessions},
        })
