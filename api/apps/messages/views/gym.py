"""The gym's own side of messages: the reminders it has sent, and how its WhatsApp is set up."""
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.tenancy import ADMIN, DESK, GymViewMixin

from ..accounts import account_for, whatsapp_mode
from ..models import Message
from ..serializers import GymWhatsAppSerializer, MessageSerializer


class MessageViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The reminders a gym has sent its members, newest first.

    Read-only everywhere: messages go out with the daily job, so there is nothing for a screen to post.
    Trainers and members are out because a dues reminder says the amount.
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
