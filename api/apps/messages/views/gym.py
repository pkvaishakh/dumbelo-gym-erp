"""The gym's own side of messages: the ones it has sent, how its WhatsApp is set up, and its message switches."""
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.tenancy import ADMIN, DESK, GymViewMixin

from .. import automation
from ..accounts import account_for, whatsapp_mode
from ..models import Message, NotificationRule
from ..serializers import GymWhatsAppSerializer, MessageSerializer, RuleSerializer, SwitchSerializer


class MessageViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The messages a gym has sent, newest first.

    Read-only everywhere: messages go out by themselves, so there is nothing for a screen to post. Trainers and
    members are out because a dues reminder says the amount; the desk sees only its branches' members' messages.
    """

    serializer_class = MessageSerializer
    roles = {"*": DESK}
    filterset_fields = ["member", "kind", "status"]

    def get_queryset(self):
        qs = Message.objects.filter(gym=self.gym).select_related("member")
        return self.in_my_branches(qs, "member__home_branch")


@extend_schema(tags=["gym"])
class GymWhatsAppView(GymViewMixin, APIView):
    """More → Settings → WhatsApp: whether messages go from Rackline's number, the gym's own or not at all, the
    number, and whether it works. Admins only; set up by Rackline, so there is nothing here to change."""

    roles = {"*": ADMIN}

    @extend_schema(responses=GymWhatsAppSerializer)
    def get(self, request):
        answer = GymWhatsAppSerializer.of(whatsapp_mode(self.gym), account_for(self.gym))
        return Response(GymWhatsAppSerializer(answer).data)


def _kind(kind: str, allowed) -> str:
    if kind not in allowed:
        raise Http404
    return kind


@extend_schema(tags=["gym"])
class GymMessagesView(GymViewMixin, APIView):
    """More → Settings → Messages: each of the gym's messages, on or paused, and when it goes out. Admins only.
    When is Rackline's to set, so it is only shown here."""

    roles = {"*": ADMIN}

    @extend_schema(responses=RuleSerializer(many=True))
    def get(self, request):
        rules = automation.rules_for(self.gym)
        return Response(RuleSerializer([rules[k] for k in NotificationRule.GYM_KINDS], many=True).data)


@extend_schema(tags=["gym"], parameters=[OpenApiParameter("kind", str, OpenApiParameter.PATH, enum=list(NotificationRule.GYM_KINDS))])
class GymMessageView(GymViewMixin, APIView):
    """Pause or Resume one of the gym's messages, at every branch. Pausing stops the messages, not the desk's
    reminder list. Audited: it decides what members and staff hear from the gym."""

    roles = {"*": ADMIN}

    @extend_schema(request=SwitchSerializer, responses=RuleSerializer)
    def patch(self, request, kind):
        kind = _kind(kind, NotificationRule.GYM_KINDS)
        s = SwitchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = automation.rules_for(self.gym)[kind]
        row = automation.switch(self.gym, kind, s.validated_data["is_on"], rackline=False)
        after = automation.rules_for(self.gym)[kind]
        if before != after:
            record(request, "message.switched", row, automation.audit_rule(before), automation.audit_rule(after))
        return Response(RuleSerializer(after).data)
