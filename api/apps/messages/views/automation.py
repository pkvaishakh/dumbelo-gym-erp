"""The Console's side of when messages go out: Rackline's times for every gym, and one gym's own.

Rackline admins only (`RacklineViewMixin`), no X-Gym. Every change is audited, against its gym where it has one.
The jobs read these on their next tick: nothing restarts.
"""
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.errors import RuleBroken
from apps.core.rackline import RacklineViewMixin
from apps.gyms.models import Gym

from .. import automation
from ..models import AutomationSchedule, WhatsAppTemplate
from ..serializers import AutomationScheduleSerializer, GymTimesSerializer, RuleSerializer

GYM_ID = OpenApiParameter("gym_id", int, OpenApiParameter.PATH, description="The gym's id")
KIND = OpenApiParameter("kind", str, OpenApiParameter.PATH, enum=[k for k, _ in WhatsAppTemplate.KINDS])


@extend_schema(tags=["platform"])
class AutomationView(RacklineViewMixin, APIView):
    """Console → Automation: the hour reminders go out on each gym's clock, how many days before a plan ends
    members are warned, and the hour on a billing day invoices are written. Whole hours only."""

    @extend_schema(responses=AutomationScheduleSerializer)
    def get(self, request):
        return Response(AutomationScheduleSerializer(AutomationSchedule.current()).data)

    @extend_schema(request=AutomationScheduleSerializer, responses=AutomationScheduleSerializer)
    def patch(self, request):
        s = AutomationScheduleSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        before = automation.audit_schedule(AutomationSchedule.current())
        schedule = automation.change_schedule(by=request.user, **s.validated_data)
        if before != automation.audit_schedule(schedule):
            record(request, "automation.changed", schedule, before, automation.audit_schedule(schedule))
        return Response(AutomationScheduleSerializer(schedule).data)


class _GymMessages(RacklineViewMixin, APIView):
    def gym(self) -> Gym:
        return get_object_or_404(Gym, pk=self.kwargs["gym_id"])


@extend_schema(tags=["platform"], parameters=[GYM_ID])
class GymMessageTimesView(_GymMessages):
    """A gym's messages as Rackline sees them: on or paused, and when each goes out (Rackline's times, or the
    gym's own where a Rackline admin set them)."""

    @extend_schema(responses=RuleSerializer(many=True))
    def get(self, request, gym_id):
        rules = automation.rules_for(self.gym())
        return Response(RuleSerializer(list(rules.values()), many=True).data)


@extend_schema(tags=["platform"], parameters=[GYM_ID, KIND])
class GymMessageTimeView(_GymMessages):
    @extend_schema(request=GymTimesSerializer, responses=RuleSerializer)
    def patch(self, request, gym_id, kind):
        """Set this gym's hour (and, for a plan ending soon, its days) in place of Rackline's; both null is Use
        Rackline's Times. Pause or Resume (`is_on`) only for the messages Rackline sends the gym's owner."""
        gym = self.gym()
        if kind not in dict(WhatsAppTemplate.KINDS):
            raise Http404
        s = GymTimesSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        if not v:
            raise RuleBroken("nothing_to_change", "Pick a time, or Pause or Resume")
        before = automation.rules_for(gym)[kind]
        with transaction.atomic():
            row = None
            if "is_on" in v:
                row = automation.switch(gym, kind, v["is_on"], rackline=True)
            if times := {k: v[k] for k in ("hour", "days_ahead") if k in v}:
                row = automation.set_times(gym, kind, **times)
        after = automation.rules_for(gym)[kind]
        if before != after:
            record(request, "message.changed", row, automation.audit_rule(before), automation.audit_rule(after), gym=gym)
        return Response(RuleSerializer(after).data)
