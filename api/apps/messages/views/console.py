"""The Console's WhatsApp: accounts (Rackline's shared number and gyms' own) and their templates.

Rackline admins only (`RacklineViewMixin`), no X-Gym. Never deleted. Credentials go in and never come out, and
the audit log says only which ones changed.
"""
from django.db.models import OuterRef
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record
from apps.core.queries import count_of
from apps.core.rackline import RacklineViewMixin

from .. import accounts
from ..accounts import WHERE
from ..models import WhatsAppAccount, WhatsAppTemplate
from ..serializers import (
    CredentialsSerializer, MessageKindSerializer, WhatsAppAccountChangeSerializer, WhatsAppAccountCreateSerializer,
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
