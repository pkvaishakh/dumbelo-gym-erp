"""The Console's WhatsApp: accounts (Rackline's shared number and gyms' own), their templates, and the log of every
message sent.

Rackline admins only (`RacklineViewMixin`), no X-Gym. Never deleted. Credentials go in and never come out, and
the audit log says only which ones changed.
"""
import re
from datetime import date, timedelta

from django.db.models import Count, OuterRef, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core import clock
from apps.core.params import Pages, open_days
from apps.core.queries import count_of
from apps.core.rackline import RacklineViewMixin

from .. import accounts, usage
from ..accounts import WHERE
from ..models import Message, WhatsAppAccount, WhatsAppTemplate
from ..serializers import (
    ConsoleMessageSerializer, ConsoleUsageSerializer, CredentialsSerializer, GymUsageRowSerializer, MessageKindSerializer, WhatsAppAccountChangeSerializer, WhatsAppAccountCreateSerializer,
    WhatsAppAccountSerializer, WhatsAppTemplateInputSerializer, WhatsAppTemplateSerializer, message_kinds,
)


def _where(account: WhatsAppAccount) -> dict:
    return {field: getattr(account, field) for field in WHERE}


def _template(t: WhatsAppTemplate) -> dict:
    return {f: getattr(t, f) for f in ("kind", "name", "language", "category", "body", "parameters", "status")}


@extend_schema(tags=["platform"])
class WhatsAppAccountViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                             mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """WhatsApp accounts: Rackline's shared number first, then gyms' own. Filter with `?gym=` or `?status=`."""

    serializer_class = WhatsAppAccountSerializer
    filterset_fields = ["gym", "status"]
    http_method_names = ["get", "post", "patch", "head", "options"]  # no PUT, and never DELETE

    def get_queryset(self):
        templates = count_of(WhatsAppTemplate.objects.filter(account=OuterRef("pk")))
        return (WhatsAppAccount.objects.defer(*WhatsAppAccount.SECRET_FIELDS).select_related("gym")
                .annotate(template_count=templates))

    def _answer(self, account, status=200):
        return Response(self.get_serializer(self.get_queryset().get(pk=account.pk)).data, status=status)

    @extend_schema(request=WhatsAppAccountCreateSerializer, responses={201: WhatsAppAccountSerializer})
    def create(self, request, *args, **kwargs):
        """Add Account. Nothing is checked with Meta until Test Connection."""
        s = WhatsAppAccountCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        account = accounts.add_account(**s.validated_data)
        record(request, "whatsapp_account.added", account, None, {**_where(account), "credentials": ["access_token", "app_secret"]},
               gym=account.gym)
        return self._answer(account, status=201)

    @extend_schema(request=WhatsAppAccountChangeSerializer, responses=WhatsAppAccountSerializer)
    def partial_update(self, request, *args, **kwargs):
        """New ids or display number. New ids mean checking it again."""
        account = self.get_object()
        s = WhatsAppAccountChangeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = _where(account)
        account = accounts.change_account(account, **s.validated_data)
        if before != _where(account):
            record(request, "whatsapp_account.changed", account, before, _where(account), gym=account.gym)
        return self._answer(account)

    def update(self, request, *args, **kwargs):  # PATCH only; http_method_names already turns PUT away
        return self.partial_update(request, *args, **kwargs)

    @extend_schema(request=CredentialsSerializer, responses=WhatsAppAccountSerializer)
    @action(detail=True, methods=["post"], url_path="replace-credentials")
    def replace_credentials(self, request, pk=None):
        """New access token, app secret or both. The audit log says which changed, never what to."""
        account = self.get_object()
        s = CredentialsSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        changed = accounts.replace_credentials(account, **s.validated_data)
        record(request, "whatsapp_account.credentials_replaced", account, None, {"credentials": changed}, gym=account.gym)
        return self._answer(account)

    @extend_schema(request=None, responses=WhatsAppAccountSerializer)
    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test Connection: asks Meta for the number's details. Sends no message."""
        account = self.get_object()
        before = account.status
        account = accounts.test_connection(account)
        record(request, "whatsapp_account.tested", account, {"status": before}, {"status": account.status}, gym=account.gym)
        return self._answer(account)


@extend_schema(tags=["platform"])
class WhatsAppTemplateViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                              mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """An account's templates (`?account=`), by message. Never deleted: one Meta no longer sends is Disabled."""

    serializer_class = WhatsAppTemplateSerializer
    filterset_fields = ["account", "kind", "status"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return WhatsAppTemplate.objects.select_related("account__gym")

    def _audit(self, request, action_name, template, before):
        if before != _template(template):
            record(request, action_name, template, before, _template(template), gym=template.account.gym)

    @extend_schema(request=WhatsAppTemplateInputSerializer, responses={201: WhatsAppTemplateSerializer})
    def create(self, request, *args, **kwargs):
        s = WhatsAppTemplateInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        template = accounts.save_template(None, **s.validated_data)
        self._audit(request, "whatsapp_template.added", template, None)
        return Response(WhatsAppTemplateSerializer(template).data, status=201)

    @extend_schema(request=WhatsAppTemplateInputSerializer, responses=WhatsAppTemplateSerializer)
    def partial_update(self, request, *args, **kwargs):
        """Edit Template: what's left out stays. Its status is copied from Meta's dashboard."""
        template = self.get_object()
        before = _template(template)
        s = WhatsAppTemplateInputSerializer(template, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        fields = {k: v for k, v in s.validated_data.items() if k != "account"}
        template = accounts.save_template(template, **fields)
        self._audit(request, "whatsapp_template.changed", template, before)
        return Response(WhatsAppTemplateSerializer(template).data)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @extend_schema(responses=MessageKindSerializer(many=True), filters=False)
    @action(detail=False, methods=["get"], pagination_class=None)
    def kinds(self, request):
        """The messages Rackline sends and the details each can fill a template with. A fixed list of seven."""
        return Response(MessageKindSerializer(message_kinds(), many=True).data)


_LOG_FILTERS = [
    OpenApiParameter("q", str, description="The number it went to (4 digits or more), Meta's message id, or the error, 2 characters or more"),
    OpenApiParameter("from", str, description="Sent on or after this day (India time), YYYY-MM-DD"),
    OpenApiParameter("to", str, description="Sent on or before this day (India time), YYYY-MM-DD"),
]


@extend_schema(tags=["platform"])
@extend_schema_view(list=extend_schema(parameters=_LOG_FILTERS))
class ConsoleMessageViewSet(RacklineViewMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Console → WhatsApp log: every message sent, newest first, across gyms. Filter by gym, WhatsApp account,
    template, message and status, between two days, or search with `q`. Read-only. Shows no names and no words:
    a message says who it was to and what they owe, and that is the gym's (only the number's last 4 digits)."""

    serializer_class = ConsoleMessageSerializer
    filterset_fields = ["gym", "account", "template", "kind", "status"]

    def get_queryset(self):
        qs = (Message.objects.select_related("gym", "account", "template")
              .defer("text", "parameters", *(f"account__{f}" for f in WhatsAppAccount.SECRET_FIELDS))
              .order_by("-created_at", "-id"))
        first, last = open_days(self.request)
        if first:  # days on Rackline's clock (no gym: India time)
            qs = qs.filter(created_at__gte=clock.day_bounds(None, first)[0])
        if last:
            qs = qs.filter(created_at__lt=clock.day_bounds(None, last)[1])
        return _search(qs, self.request.query_params.get("q", ""))


def _search(qs, text: str):
    """Digits find the number it went to by its end, or Meta's error code; anything else Meta's message id, error
    code or error words."""
    text = text.strip()
    if len(text) < 2:
        return qs
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 4 and not re.search(r"[A-Za-z]", text):
        return qs.filter(Q(to__endswith=digits[-10:]) | Q(error_code=digits))
    return qs.filter(Q(provider_id__icontains=text) | Q(error_code__iexact=text) | Q(error__icontains=text))


MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def _month(value: str | None) -> date:
    """The first day of `?month=YYYY-MM`; Rackline's this month when it's left out."""
    if not value:
        return timezone.localdate().replace(day=1)
    if not (m := MONTH.match(value)):
        raise ValidationError({"month": ["Use YYYY-MM"]})
    return date(int(m[1]), int(m[2]), 1)


@extend_schema(tags=["platform"])
class ConsoleUsageView(RacklineViewMixin, APIView):
    """Console → WhatsApp usage: each gym's messages delivered from Rackline's shared number in a month (each in the
    gym's own days, as its invoice counts them) and what they came to, the biggest first, with the month's totals.
    Counts and Rackline's money only. A fixed number of queries whatever the number of gyms."""

    @extend_schema(responses=ConsoleUsageSerializer, parameters=[
        OpenApiParameter("month", str, description="YYYY-MM; this month when left out"),
        OpenApiParameter("limit", int, description="Gyms a page, at most 100"), OpenApiParameter("offset", int),
    ])
    def get(self, request):
        first = _month(request.query_params.get("month"))
        messages = usage.delivered_anywhere(first, clock.add_months(first, 1) - timedelta(days=1))
        pages = Pages()
        page = pages.paginate_queryset(usage.by_gym(messages), request, view=self)
        answer = pages.get_paginated_response(GymUsageRowSerializer(page, many=True).data).data
        totals = messages.aggregate(messages=Count("id"), amount_paise=Coalesce(Sum("rate_paise"), 0))
        return Response(ConsoleUsageSerializer({"month": f"{first:%Y-%m}", **totals, **answer}).data)
