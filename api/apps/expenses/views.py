from django.db.models import Count, Exists, Min, OuterRef, Q, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.audit.models import record
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, DESK, GymViewMixin
from apps.gyms.models import GymRole

from . import services
from .models import Expense, ExpenseDue, RecurringExpense
from .serializers import ExpenseDueSerializer, ExpenseSerializer, PayDueSerializer, RecurringExpenseSerializer, paid_for

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
    day's payments; only admins see longer spans, edit or remove. An expense that paid a bill or a salary is
    changed from there, never here, so the two can't disagree."""

    serializer_class = ExpenseSerializer
    roles = {"list": DESK, "retrieve": DESK, "create": DESK, "totals": DESK, "today": DESK, "*": ADMIN}
    filterset_fields = ["branch", "category", "method"]

    def get_queryset(self):
        qs = self.in_my_branches(Expense.objects.filter(gym=self.gym).select_related("branch", "due", "salary_payment"))
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

    def _not_linked(self, expense):
        kind = paid_for(expense)
        if kind == "bill":
            raise RuleBroken("paid_a_bill", "This expense paid a bill. Change it from Dues.")
        if kind == "salary":
            raise RuleBroken("paid_a_salary", "This expense paid a salary. Change it from Payroll.")

    def perform_update(self, serializer):
        self._not_linked(serializer.instance)
        serializer.save()

    def perform_destroy(self, expense):
        self._not_linked(expense)
        expense.delete()

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


def _snapshot(rule):
    return {"name": rule.name, "amount_paise": rule.amount_paise, "frequency": rule.frequency, "starts": str(rule.starts),
            "ends": str(rule.ends) if rule.ends else None, "is_active": rule.is_active}


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("active", bool, description="Running (true) or stopped (false)")]))
class RecurringExpenseViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """Rent, bills and subscriptions the gym pays again and again. Admins only. Never deleted: stopped instead,
    and stopping skips the dates still to come."""

    serializer_class = RecurringExpenseSerializer
    roles = {"*": ADMIN}
    filterset_fields = ["branch", "category"]

    def get_queryset(self):
        qs = RecurringExpense.objects.filter(gym=self.gym).select_related("branch").annotate(
            next_due=Min("dues__due_on", filter=Q(dues__status=ExpenseDue.DUE)),
            dates_fixed=Exists(ExpenseDue.objects.filter(recurring=OuterRef("pk"))))
        if (active := self.request.query_params.get("active")) in ("true", "false"):
            qs = qs.filter(is_active=active == "true")
        return self.in_my_branches(qs)

    def perform_create(self, serializer):
        rule = serializer.save()
        services.sync_dues(self.gym)
        record(self.request, "recurring_expense.added", rule, None, _snapshot(rule))
        serializer.instance = self.get_queryset().get(pk=rule.pk)  # with its next date

    def perform_update(self, serializer):
        before = _snapshot(serializer.instance)
        if not serializer.instance.is_active:
            raise RuleBroken("stopped", "This one is stopped. Add a new one instead.")
        rule = serializer.save()
        services.reconcile(rule, clock.today(self.gym))
        record(self.request, "recurring_expense.changed", rule, before, _snapshot(rule))
        serializer.instance = self.get_queryset().get(pk=rule.pk)

    @extend_schema(request=None, responses=RecurringExpenseSerializer)
    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        """No more dates from today on: the ones still to come are skipped; late ones stay to be paid or skipped."""
        rule = self.get_object()
        if not rule.is_active:
            raise RuleBroken("stopped", "This one is already stopped")
        before = _snapshot(rule)
        rule.is_active = False
        rule.save(update_fields=["is_active", "updated_at"])
        services.reconcile(rule, clock.today(self.gym))
        record(request, "recurring_expense.stopped", rule, before, _snapshot(rule))
        return Response(self.get_serializer(self.get_queryset().get(pk=rule.pk)).data)


_DUE_STATES = {
    # state -> (filter, order). "open" is what Home counts: inside its reminder days, not paid or skipped.
    "open": (lambda t: Q(status=ExpenseDue.DUE, remind_on__lte=t), ["due_on", "id"]),
    "overdue": (lambda t: Q(status=ExpenseDue.DUE, due_on__lt=t), ["due_on", "id"]),
    "upcoming": (lambda t: Q(status=ExpenseDue.DUE, remind_on__gt=t), ["due_on", "id"]),
    "paid": (lambda t: Q(status=ExpenseDue.PAID), ["-due_on", "-id"]),
    "skipped": (lambda t: Q(status=ExpenseDue.SKIPPED), ["-due_on", "-id"]),
    "all": (lambda t: Q(), ["-due_on", "-id"]),
}

BillsDue = inline_serializer("BillsDue", {"count": serializers.IntegerField(), "overdue": serializers.IntegerField(), "total_paise": serializers.IntegerField()})


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("state", str, enum=list(_DUE_STATES), description="open (default): inside its reminder days and not paid"),
    OpenApiParameter("branch", int), OpenApiParameter("recurring", int, description="One recurring expense's dates"),
]))
class ExpenseDueViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The dates recurring expenses are due, to pay or skip. Admins only. Reading writes any dates not yet listed."""

    serializer_class = ExpenseDueSerializer
    roles = {"*": ADMIN}

    def initial(self, request, *a, **kw):
        super().initial(request, *a, **kw)
        if request.method == "GET" and not getattr(self, "swagger_fake_view", False):
            services.sync_dues(self.gym)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            ctx["today"] = clock.today(self.gym)
        return ctx

    def get_queryset(self):
        qs = self.in_my_branches(ExpenseDue.objects.filter(gym=self.gym).select_related("recurring__branch", "expense"), "recurring__branch")
        if self.action != "list":
            return qs
        state = self.request.query_params.get("state") or "open"
        if state not in _DUE_STATES:
            raise ValidationError({"state": [f"Use one of {', '.join(_DUE_STATES)}"]})
        rule, order = _DUE_STATES[state]
        qs = qs.filter(rule(clock.today(self.gym))).order_by(*order)
        if (branch := int_param(self.request, "branch")) is not None:
            qs = qs.filter(recurring__branch_id=branch)
        if (recurring := int_param(self.request, "recurring")) is not None:
            qs = qs.filter(recurring_id=recurring)
        return qs

    @extend_schema(request=PayDueSerializer, responses=ExpenseDueSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Pay this date. The amount can differ from the usual one (a bill that varies); it becomes an expense."""
        due = self.get_object()
        body = PayDueSerializer(data=request.data, context=self.get_serializer_context())
        body.is_valid(raise_exception=True)
        d = body.validated_data
        expense = services.pay_due(due, amount_paise=d["amount_paise"], method=d["method"], paid_on=d.get("paid_on") or clock.today(self.gym),
                                   by=self.me, note=d.get("note", ""))
        record(request, "expense_due.paid", due, None, {"amount_paise": expense.amount_paise, "expense": expense.id})
        return Response(self.get_serializer(self.get_queryset().get(pk=due.pk)).data)

    @extend_schema(request=None, responses=ExpenseDueSerializer)
    @action(detail=True, methods=["post"])
    def skip(self, request, pk=None):
        """This date won't be paid: it leaves the list and nothing is spent."""
        due = services.skip_due(self.get_object())
        record(request, "expense_due.skipped", due, {"status": ExpenseDue.DUE}, {"status": due.status})
        return Response(self.get_serializer(self.get_queryset().get(pk=due.pk)).data)

    @extend_schema(parameters=[OpenApiParameter("branch", int)], responses=BillsDue)
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """The open bills in one figure: how many, how many are late, and the amount."""
        return Response(services.bills_due(self.gym, clock.today(self.gym), int_param(request, "branch")))
