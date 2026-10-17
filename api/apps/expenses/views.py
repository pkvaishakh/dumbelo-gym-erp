from django.db.models import Count, Q, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, DESK, GymViewMixin
from apps.gyms.models import Branch, GymRole

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.none())
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "branch", "branch_name", "category", "amount_paise", "method", "paid_to", "note", "spent_on"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            branches = Branch.objects.filter(gym=req.gym)
            ids = req.gym_role.branch_ids()  # the desk adds expenses for its own branches only
            self.fields["branch"].queryset = branches if ids is None else branches.filter(id__in=ids)

    def validate_amount_paise(self, v):
        if v <= 0:
            raise serializers.ValidationError("Enter an amount above zero")
        return v

    def create(self, data):
        req = self.context["request"]
        return Expense.objects.create(gym=req.gym, created_by=req.gym_role, **data)


_FILTERS = [
    OpenApiParameter("month", str, description="YYYY-MM"),
    OpenApiParameter("from", str, description="First day spent, YYYY-MM-DD"),
    OpenApiParameter("to", str, description="Last day spent, YYYY-MM-DD"),
    OpenApiParameter("q", str, description="Who it was paid to, or the note"),
]


@extend_schema_view(list=extend_schema(parameters=_FILTERS), totals=extend_schema(parameters=_FILTERS))
class ExpenseViewSet(GymViewMixin, viewsets.ModelViewSet):
    """What the gym spends. Filter by ?month=2026-10 or ?from=&to=, branch, category, method, or search with q.
    Receptionists see and add their branches' expenses one day at a time (today when no day is given), like the
    day's payments; only admins see longer spans, edit or remove."""

    serializer_class = ExpenseSerializer
    roles = {"list": DESK, "retrieve": DESK, "create": DESK, "totals": DESK, "today": DESK, "*": ADMIN}
    filterset_fields = ["branch", "category", "method"]

    def get_queryset(self):
        qs = self.in_my_branches(Expense.objects.filter(gym=self.gym).select_related("branch"))
        p = self.request.query_params
        desk = self.me.role not in (GymRole.ADMIN, "support")
        if month := p.get("month"):
            if desk:
                raise RuleBroken("not_allowed", "You can see one day's expenses at a time")
            d = clock.parse_date(month + "-01", None)
            qs = qs.filter(spent_on__gte=d, spent_on__lt=clock.add_months(d, 1))
        first = clock.parse_date(p.get("from"), None, field="from")
        last = clock.parse_date(p.get("to"), None, field="to")
        if first and last and first > last:
            raise ValidationError({"from": ["Pick a start date on or before the end date"]})
        if desk and self.action in ("list", "totals"):
            if first and last and first != last:
                raise RuleBroken("not_allowed", "You can see one day's expenses at a time")
            first = last = first or last or clock.today(self.gym)
        if first:
            qs = qs.filter(spent_on__gte=first)
        if last:
            qs = qs.filter(spent_on__lte=last)
        if q := p.get("q", "").strip():
            qs = qs.filter(Q(paid_to__icontains=q) | Q(note__icontains=q))
        return qs

    @action(detail=False, methods=["get"])
    def totals(self, request):
        """Totals by category for the same filters."""
        qs = self.filter_queryset(self.get_queryset())
        rows = qs.values("category").annotate(t=Sum("amount_paise")).order_by("-t")
        return Response({"total_paise": sum(r["t"] for r in rows), "by_category": {r["category"]: r["t"] for r in rows}})

    @extend_schema(parameters=[OpenApiParameter("branch", int)], responses=inline_serializer("ExpensesToday", {
        "date": serializers.DateField(), "total_paise": serializers.IntegerField(), "count": serializers.IntegerField()}))
    @action(detail=False, methods=["get"])
    def today(self, request):
        """Spent today in the caller's branches: a total and a count, for the receptionist's Home."""
        day = clock.today(self.gym)
        qs = self.in_my_branches(Expense.objects.filter(gym=self.gym, spent_on=day))
        if (branch := int_param(request, "branch")) is not None:
            qs = qs.filter(branch=branch)
        agg = qs.aggregate(t=Sum("amount_paise"), n=Count("id"))
        return Response({"date": day, "total_paise": agg["t"] or 0, "count": agg["n"]})
