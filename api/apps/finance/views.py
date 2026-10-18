from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.audit.models import record
from apps.core import clock
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, GymViewMixin
from apps.members.serializers import VoidSerializer

from . import services
from .models import Account, MoneyMove
from .serializers import AccountSerializer, BranchAccountSerializer, MoneyMoveSerializer


def _snapshot(a: Account) -> dict:
    return {"kind": a.kind, "label": a.label, "bank_name": a.bank_name, "account_number": a.account_number, "ifsc": a.ifsc,
            "opening_balance_paise": a.opening_balance_paise, "is_active": a.is_active}


class AccountBrief(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    balance_paise = serializers.IntegerField()
    shared_with = serializers.ListField(child=serializers.CharField(), help_text="Other branches that use this bank account")


Overview = inline_serializer("MoneyOverview", {
    "totals": inline_serializer("MoneyTotals", {"cash_paise": serializers.IntegerField(), "bank_paise": serializers.IntegerField(),
                                                "total_paise": serializers.IntegerField()}),
    "branches": inline_serializer("BranchMoney", {"id": serializers.IntegerField(), "name": serializers.CharField(),
                                                  "cash": AccountBrief(allow_null=True), "bank": AccountBrief(allow_null=True)}, many=True),
    "accounts": AccountSerializer(many=True),
})


Statement = inline_serializer("AccountStatement", {
    "from": serializers.DateField(help_text="The first day shown: the month's first, or the day the account was added"),
    "to": serializers.DateField(help_text="The last day shown: the month's last, or today"),
    "opening_paise": serializers.IntegerField(help_text="The balance before the first day"),
    "closing_paise": serializers.IntegerField(help_text="The balance after the last day"),
    "in_paise": serializers.IntegerField(), "out_paise": serializers.IntegerField(),
    "entries": inline_serializer("StatementEntry", {
        "kind": serializers.ChoiceField(choices=["payment", "expense", "move"]), "id": serializers.IntegerField(),
        "member": serializers.IntegerField(allow_null=True, help_text="Payments: the member who paid"),
        "on": serializers.DateField(), "title": serializers.CharField(), "meta": serializers.CharField(),
        "amount_paise": serializers.IntegerField(help_text="Signed: above zero came in, below zero went out"),
        "balance_paise": serializers.IntegerField(help_text="The balance after this entry"),
    }, many=True),
})


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("kind", str, enum=[k for k, _ in Account.KINDS]), OpenApiParameter("is_active", bool)]))
class AccountViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """Each branch's cash in hand and the gym's bank accounts, with their balances and the branches each bank account
    serves. Admins only. Never deleted: deactivated, once empty."""

    serializer_class = AccountSerializer
    roles = {"*": ADMIN}
    pagination_class = None  # a cash account per branch and a few bank accounts: pickers and the screen need them all
    filterset_fields = ["kind", "is_active"]

    def get_queryset(self):
        return services.listed(self.gym)

    def _branches_changed(self, account, moved):
        if moved:
            record(self.request, "account.branches_changed", account, None, {"branches": sorted(account.links.values_list("branch_id", flat=True)), "moved": moved})

    @transaction.atomic
    def perform_create(self, serializer):
        branches = serializer.validated_data.pop("branches", None)
        account = serializer.save()
        record(self.request, "account.added", account, None, _snapshot(account))
        if branches:
            self._branches_changed(account, services.set_branches(account, branches))
        serializer.instance = self.get_queryset().get(pk=account.pk)

    @transaction.atomic
    def perform_update(self, serializer):
        before = _snapshot(serializer.instance)
        branches = serializer.validated_data.pop("branches", None)
        account = serializer.save()
        if (after := _snapshot(account)) != before:
            record(self.request, "account.changed", account, before, after)
        if branches is not None and account.kind == Account.BANK:  # cash belongs to its branch: validation refused any others
            self._branches_changed(account, services.set_branches(account, branches))
        serializer.instance = self.get_queryset().get(pk=account.pk)

    @extend_schema(request=None, responses=AccountSerializer)
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Stop using it. It must hold nothing; branches that used it are left without a bank account."""
        account = self.get_object()
        branches = services.deactivate(account)
        record(request, "account.deactivated", account, {"is_active": True, "branches": branches}, {"is_active": False})
        return Response(self.get_serializer(self.get_queryset().get(pk=account.pk)).data)

    @extend_schema(request=None, responses=AccountSerializer)
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        account = self.get_object()
        if not account.is_active:
            account.is_active = True
            account.save(update_fields=["is_active", "updated_at"])
            record(request, "account.activated", account, {"is_active": False}, {"is_active": True})
        return Response(self.get_serializer(self.get_queryset().get(pk=account.pk)).data)

    @extend_schema(request=BranchAccountSerializer, responses=Overview)
    @action(detail=False, methods=["post"], url_path="branch")
    def set_branch(self, request):
        """Give a branch the bank account its new UPI, card and bank money goes into (or none). Old money stays put."""
        body = BranchAccountSerializer(data=request.data, context=self.get_serializer_context())
        body.is_valid(raise_exception=True)
        branch, account = body.validated_data["branch"], body.validated_data["account"]
        before = services.set_branch_account(branch, account)
        if before != (account.pk if account else None):
            record(request, "branch.bank_account_changed", branch, {"account": before}, {"account": account.pk if account else None})
        return self.overview(request)

    @extend_schema(parameters=[OpenApiParameter("month", str, description="YYYY-MM; this month when left out")], responses=Statement)
    @action(detail=True, methods=["get"])
    def statement(self, request, pk=None):
        """One month of this account, entry by entry with the balance after each, to check against the bank's
        statement or the cash counted at the desk."""
        account = self.get_object()
        month = request.query_params.get("month")
        first = clock.parse_date(f"{month}-01", None, field="month") if month else clock.today(self.gym).replace(day=1)
        return Response(services.statement(account, first))

    @extend_schema(responses=Overview)
    @action(detail=False, methods=["get"])
    def overview(self, request):
        """The money screen in one call: totals with each account counted once, each branch's cash and bank account,
        and every account."""
        body = services.overview(self.gym)
        body["accounts"] = AccountSerializer(body["accounts"], many=True, context=self.get_serializer_context()).data
        return Response(body)


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("account", int, description="Moves in or out of this account"),
    OpenApiParameter("from", str, description="First day, YYYY-MM-DD"), OpenApiParameter("to", str, description="Last day, YYYY-MM-DD"),
]))
class MoneyMoveViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Deposits, withdrawals and transfers between accounts or branches: money that is neither income nor spending.
    Admins only. A wrong one is voided with a reason, never edited or deleted."""

    serializer_class = MoneyMoveSerializer
    roles = {"*": ADMIN}
    filterset_fields = ["kind", "voided"]

    def get_queryset(self):
        qs = MoneyMove.objects.filter(gym=self.gym).select_related("from_account__branch", "to_account__branch", "created_by__user")
        if (account := int_param(self.request, "account")) is not None:
            qs = qs.filter(Q(from_account_id=account) | Q(to_account_id=account))
        p = self.request.query_params
        first = clock.parse_date(p.get("from"), None, field="from")
        last = clock.parse_date(p.get("to"), None, field="to")
        if first and last and first > last:
            raise ValidationError({"from": ["Pick a start date on or before the end date"]})
        if first:
            qs = qs.filter(moved_on__gte=first)
        if last:
            qs = qs.filter(moved_on__lte=last)
        return qs

    def perform_create(self, serializer):
        d = serializer.validated_data
        m = services.move(self.gym, kind=d["kind"], amount_paise=d["amount_paise"], moved_on=d.get("moved_on") or clock.today(self.gym), by=self.me,
                          from_account=d.get("from_account"), to_account=d.get("to_account"), note=d.get("note", ""))
        record(self.request, "money_move.added", m, None, {"kind": m.kind, "from": m.from_account_id, "to": m.to_account_id, "amount_paise": m.amount_paise})
        serializer.instance = self.get_queryset().get(pk=m.pk)

    @extend_schema(request=VoidSerializer, responses=MoneyMoveSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """It was wrong: the money goes back where it came from. Kept, marked voided, with the reason."""
        body = VoidSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        m = services.void(self.get_object(), body.validated_data["reason"])
        record(request, "money_move.voided", m, {"voided": False}, {"voided": True, "reason": m.void_reason})
        return Response(self.get_serializer(self.get_queryset().get(pk=m.pk)).data)
