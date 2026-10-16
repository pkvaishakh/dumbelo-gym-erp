from django.db.models import Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core import clock
from apps.core.tenancy import ADMIN, GymViewMixin
from apps.gyms.models import Branch

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
            self.fields["branch"].queryset = Branch.objects.filter(gym=req.gym)

    def validate_amount_paise(self, v):
        if v <= 0:
            raise serializers.ValidationError("Enter an amount above zero")
        return v

    def create(self, data):
        req = self.context["request"]
        return Expense.objects.create(gym=req.gym, created_by=req.gym_role, **data)


_MONTH = OpenApiParameter("month", str, description="YYYY-MM")


@extend_schema_view(list=extend_schema(parameters=[_MONTH]), totals=extend_schema(parameters=[_MONTH]))
class ExpenseViewSet(GymViewMixin, viewsets.ModelViewSet):
    """What the gym spends. Admins only. Filter by ?month=2026-10, branch or category."""

    serializer_class = ExpenseSerializer
    roles = {"*": ADMIN}
    filterset_fields = ["branch", "category", "method"]

    def get_queryset(self):
        qs = Expense.objects.filter(gym=self.gym).select_related("branch")
        month = self.request.query_params.get("month")
        if month:
            d = clock.parse_date(month + "-01", None)
            qs = qs.filter(spent_on__gte=d, spent_on__lt=clock.add_months(d, 1))
        return qs

    @action(detail=False, methods=["get"])
    def totals(self, request):
        """Totals by category for the same filters."""
        qs = self.filter_queryset(self.get_queryset())
        rows = qs.values("category").annotate(t=Sum("amount_paise")).order_by("-t")
        return Response({"total_paise": sum(r["t"] for r in rows), "by_category": {r["category"]: r["t"] for r in rows}})
