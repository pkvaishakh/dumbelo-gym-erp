from rest_framework import mixins, viewsets

from apps.core.tenancy import DESK, GymViewMixin

from .models import Message
from .serializers import MessageSerializer


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
