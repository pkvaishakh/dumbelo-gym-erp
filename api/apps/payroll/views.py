from django.db.models import Count, F, Q, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record
from apps.core import clock
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, GymViewMixin
from apps.gyms.models import GymRole

from . import services
from .models import Payslip, SalaryRule
from .serializers import (
    DaysSerializer, LineSerializer, MonthSerializer, PaySalarySerializer, PayslipDetailSerializer, PayslipSerializer, RemoveLineSerializer,
    SalaryRuleSerializer,
)


def _rule_snapshot(rule):
    return {"pay_type": rule.pay_type, "rate_paise": rule.rate_paise, "hours_per_day": str(rule.hours_per_day), "branch": rule.branch_id,
            "items": [{"kind": i.kind, "label": i.label, "amount_paise": i.amount_paise} for i in rule.items.all()]}


def _slip_snapshot(slip):
    return {"status": slip.status, "days_present": slip.days_present, "net_paise": slip.net_paise}


def _month(request, gym):
    """?month=YYYY-MM, this month when missing."""
    value = request.query_params.get("month")
    if not value:
        return clock.today(gym).replace(day=1)
    body = MonthSerializer(data={"month": value})
    body.is_valid(raise_exception=True)
    return body.validated_data["month"]


class SalaryRuleViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    """How each staff member is paid. Admins only. `?staff=` finds one person's. Changes reach this month's draft
    payslip the next time payroll is worked out; approved payslips never change."""

    serializer_class = SalaryRuleSerializer
    roles = {"*": ADMIN}
    filterset_fields = ["staff", "branch", "pay_type"]
    pagination_class = None  # one row per staff member: a gym has tens, and the Payroll screen needs them all

    def get_queryset(self):
        return SalaryRule.objects.filter(gym=self.gym).select_related("staff__user", "branch").prefetch_related("items").order_by("staff__user__name")

    def perform_create(self, serializer):
        rule = serializer.save()
        record(self.request, "salary.set", rule, None, _rule_snapshot(rule))

    def perform_update(self, serializer):
        before = _rule_snapshot(serializer.instance)
        rule = serializer.save()
        record(self.request, "salary.changed", rule, before, _rule_snapshot(rule))


PayrollSummary = inline_serializer("PayrollSummary", {
    "month": serializers.DateField(), "payslips": serializers.IntegerField(), "drafts": serializers.IntegerField(),
    "approved": serializers.IntegerField(), "net_paise": serializers.IntegerField(), "paid_paise": serializers.IntegerField(),
    "staff_without_salary": serializers.IntegerField(),
})


@extend_schema_view(
    list=extend_schema(parameters=[OpenApiParameter("month", str, description="YYYY-MM; every month when missing"),
                                   OpenApiParameter("owed", bool, description="Only approved salaries not yet paid in full")]),
    summary=extend_schema(parameters=[OpenApiParameter("month", str, description="YYYY-MM; this month when missing"), OpenApiParameter("branch", int)],
                          responses=PayrollSummary),
)
class PayslipViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Payroll. Admins only. Work out a month (`generate`), check each payslip, add incentives, bonuses and
    deductions, approve it, and pay it in full or in parts. `?staff=` is one person's salary history."""

    roles = {"*": ADMIN}
    filterset_fields = ["staff", "status", "branch"]

    def get_serializer_class(self):
        return PayslipSerializer if self.action == "list" else PayslipDetailSerializer

    def get_queryset(self):
        qs = Payslip.objects.filter(gym=self.gym).select_related("staff__user", "branch").with_paid()
        if self.action == "list":
            if self.request.query_params.get("month"):
                qs = qs.filter(month=_month(self.request, self.gym))
            if self.request.query_params.get("owed") == "true":
                qs = qs.filter(status=Payslip.APPROVED, net_paise__gt=F("paid_total")).order_by("month", "staff__user__name")
            return qs
        return qs.select_related("approved_by__user", "gym").prefetch_related("lines", "payments__paid_by__user")

    def _answer(self, slip):
        return Response(PayslipDetailSerializer(self.get_queryset().get(pk=slip.pk), context=self.get_serializer_context()).data)

    @extend_schema(request=MonthSerializer, responses=PayslipSerializer(many=True))
    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Make or refresh the month's payslips from salary rules and check-ins. Approved ones stay as they are."""
        body = MonthSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        services.generate(self.gym, body.validated_data["month"])
        qs = Payslip.objects.filter(gym=self.gym, month=body.validated_data["month"]).select_related("staff__user", "branch").with_paid()
        return Response(PayslipSerializer(qs, many=True, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """The month in figures, and how many active staff have no salary set (they get no payslip)."""
        month = _month(request, self.gym)
        slips = Payslip.objects.filter(gym=self.gym, month=month)
        missing = GymRole.objects.filter(gym=self.gym, is_active=True, role__in=GymRole.STAFF_ROLES, salary_rule__isnull=True)
        if (branch := int_param(request, "branch")) is not None:
            slips, missing = slips.filter(branch_id=branch), missing.filter(branches=branch)
        agg = slips.aggregate(
            n=Count("id"), drafts=Count("id", filter=Q(status=Payslip.DRAFT)), approved=Count("id", filter=Q(status=Payslip.APPROVED)),
            net=Sum("net_paise"))
        paid = slips.aggregate(t=Sum("payments__amount_paise"))["t"] or 0
        missing = missing.count()
        return Response({"month": month, "payslips": agg["n"], "drafts": agg["drafts"], "approved": agg["approved"], "net_paise": agg["net"] or 0,
                         "paid_paise": paid, "staff_without_salary": missing})

    @extend_schema(request=DaysSerializer, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"])
    def days(self, request, pk=None):
        """Set the days present by hand, for a day worked without a check-in or a paid leave."""
        slip = self.get_object()
        body = DaysSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        before = _slip_snapshot(slip)
        slip = services.set_days(slip, body.validated_data["days_present"])
        record(request, "payslip.days_set", slip, before, _slip_snapshot(slip))
        return self._answer(slip)

    @extend_schema(request=LineSerializer, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"])
    def lines(self, request, pk=None):
        """Add an allowance, incentive, referral bonus or deduction to this month only."""
        slip = self.get_object()
        body = LineSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        before = _slip_snapshot(slip)
        slip = services.add_line(slip, **body.validated_data)
        record(request, "payslip.line_added", slip, before, {**_slip_snapshot(slip), "line": {k: v for k, v in body.validated_data.items()}})
        return self._answer(slip)

    @extend_schema(request=RemoveLineSerializer, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"], url_path="remove-line")
    def remove_line(self, request, pk=None):
        slip = self.get_object()
        body = RemoveLineSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        before = _slip_snapshot(slip)
        slip = services.remove_line(slip, body.validated_data["line"])
        record(request, "payslip.line_removed", slip, before, _slip_snapshot(slip))
        return self._answer(slip)

    @extend_schema(request=None, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        slip = services.approve(self.get_object(), self.me)
        record(request, "payslip.approved", slip, {"status": Payslip.DRAFT}, _slip_snapshot(slip))
        return self._answer(slip)

    @extend_schema(request=None, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        slip = services.reopen(self.get_object())
        record(request, "payslip.reopened", slip, {"status": Payslip.APPROVED}, _slip_snapshot(slip))
        return self._answer(slip)

    @extend_schema(request=PaySalarySerializer, responses=PayslipDetailSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Pay all or part of what's owed. Each payment is also an expense under Salaries."""
        slip = self.get_object()
        body = PaySalarySerializer(data=request.data, context=self.get_serializer_context())
        body.is_valid(raise_exception=True)
        d = body.validated_data
        payment = services.pay(slip, amount_paise=d["amount_paise"], method=d["method"], paid_on=d.get("paid_on") or clock.today(self.gym),
                               by=self.me, note=d.get("note", ""))
        record(request, "payslip.paid", slip, None, {"amount_paise": payment.amount_paise, "method": payment.method, "expense": payment.expense_id})
        return self._answer(slip)
