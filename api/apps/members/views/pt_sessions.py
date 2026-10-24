from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.audit.models import record
from apps.core import clock
from apps.core.tenancy import ALL, STAFF, GymViewMixin
from apps.gyms.models import GymRole

from .. import services
from ..models import PTSession, Subscription
from ..pt_serializers import MarkSessionSerializer, PTSessionSerializer, SessionNotesSerializer
from ..serializers import VoidSerializer


class PTSessionViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Personal training sessions given, each using one of a plan's sessions. Trainers mark today's for their own
    members; the desk and admins any day inside the plan, and any of them notes what it worked. A member sees their
    own. Removed ones stay, marked void."""

    serializer_class = PTSessionSerializer
    roles = {"list": ALL, "retrieve": ALL, "*": STAFF}
    filterset_fields = ["member", "subscription", "trainer", "voided"]

    def get_queryset(self):
        qs = PTSession.objects.filter(gym=self.gym).select_related("member", "subscription__plan", "trainer__user", "marked_by__user")
        role = self.me.role
        if role == GymRole.MEMBER:
            return qs.filter(member__user=self.request.user)
        if role == GymRole.TRAINER:
            return qs.filter(Q(member__trainer=self.me) | Q(subscription__trainer=self.me) | Q(trainer=self.me))
        return self.in_my_branches(qs, "member__home_branch")

    def plans_i_can_mark(self):
        """Personal training the caller may mark: a trainer's own members', the desk's branches'."""
        qs = Subscription.objects.filter(member__gym=self.gym, member__is_archived=False)
        if self.me.role == GymRole.TRAINER:
            return qs.filter(Q(member__trainer=self.me) | Q(trainer=self.me))
        return self.in_my_branches(qs, "member__home_branch")

    @extend_schema(request=MarkSessionSerializer, responses={201: PTSessionSerializer})
    def create(self, request, *args, **kwargs):
        """Mark a session given: it uses one of the plan's sessions. One a day for each plan."""
        body = MarkSessionSerializer(data=request.data, queryset=self.plans_i_can_mark())
        body.is_valid(raise_exception=True)
        on = body.validated_data.get("local_date")
        if on and self.me.role == GymRole.TRAINER and on != clock.today(self.gym):
            raise ValidationError({"local_date": ["Mark today's session. The front desk can mark an earlier one."]})
        d = body.validated_data
        s = services.mark_session(d["subscription"], by=self.me, on=on, body_parts=d.get("body_parts", ()), notes=d.get("notes", ""))
        record(request, "pt_session.marked", s, None, {"member": s.member_id, "subscription": s.subscription_id, "local_date": str(s.local_date)})
        return Response(self.get_serializer(self.get_queryset().get(pk=s.pk)).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=SessionNotesSerializer, responses=PTSessionSerializer)
    def partial_update(self, request, *args, **kwargs):
        """Change what a session worked and its notes."""
        body = SessionNotesSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        s = self.get_object()
        before = {"body_parts": s.body_parts, "notes": s.notes}
        s = services.note_session(s, **body.validated_data)
        record(request, "pt_session.updated", s, before, {"body_parts": s.body_parts, "notes": s.notes})
        return Response(self.get_serializer(self.get_queryset().get(pk=s.pk)).data)

    @extend_schema(request=VoidSerializer, responses=PTSessionSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Remove a session marked by mistake: the plan gets it back. Admins remove any; others one they marked today."""
        body = VoidSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        s = services.void_session(self.get_object(), body.validated_data["reason"], by=self.me)
        record(request, "pt_session.voided", s, {"voided": False}, {"voided": True, "reason": s.void_reason})
        return Response(self.get_serializer(self.get_queryset().get(pk=s.pk)).data)
