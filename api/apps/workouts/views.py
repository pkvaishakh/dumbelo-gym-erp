"""Workout and diet plans: one pair of views for each (the plans, and who's on them), on shared bases so both follow
the same rules."""
from django.db.models import OuterRef, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record
from apps.core.errors import RuleBroken
from apps.core.params import int_param
from apps.core.queries import count_of
from apps.core.tenancy import ALL, STAFF, GymViewMixin
from apps.gyms.models import GymRole
from apps.members.models import Member

from . import services
from .models import DietAssignment, DietPlan, WorkoutAssignment, WorkoutPlan
from .serializers import (
    AssignSerializer, DietAssignmentSerializer, DietPlanSerializer, WorkoutAssignmentSerializer, WorkoutPlanSerializer,
)

COACHES = (GymRole.ADMIN, GymRole.TRAINER)

PLAN_FILTERS = extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("q", str, description="Name or goal"),
    OpenApiParameter("mine", bool, description="Only the plans you wrote"),
    OpenApiParameter("archived", bool, description="Archived plans instead of the ones in use"),
]))
ASSIGNMENT_FILTERS = extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("member", int), OpenApiParameter("plan", int),
    OpenApiParameter("current", bool, description="Only the plans members are on now"),
]))


class CoachPlanViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                       mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """The gym's plans of one kind. All staff see every one; trainers and admins write them. Only a plan's author or
    an admin changes or archives it (is_active). Never deleted. Subclasses name the model and its assignments."""

    model = assignments = None
    roles = {"list": STAFF, "retrieve": STAFF, "*": COACHES}
    http_method_names = ["get", "post", "patch", "head", "options"]  # no PUT, and never DELETE

    def get_queryset(self):
        on_it = self.assignments.objects.filter(plan=OuterRef("pk"), ended_at__isnull=True)
        qs = self.model.objects.filter(gym=self.gym).select_related("created_by__user").annotate(members_count=count_of(on_it))
        if self.action != "list":
            return qs
        p = self.request.query_params
        qs = qs.filter(is_active=p.get("archived") != "true")
        if p.get("mine") == "true":
            qs = qs.filter(created_by=self.me)
        q = p.get("q", "").strip()
        if len(q) >= 2:
            qs = qs.filter(Q(name__icontains=q) | Q(goal__icontains=q))
        return qs

    def _saved(self, plan, code=status.HTTP_200_OK):
        """The plan as the list shows it, with its count of members on it."""
        return Response(self.get_serializer(self.get_queryset().get(pk=plan.pk)).data, status=code)

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return self._saved(s.save(gym=self.gym, created_by=self.me), status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        plan = self.get_object()
        if not services.can_change(plan, self.me):
            raise RuleBroken("not_yours", f"Only {plan.created_by.user.name} or an admin can change this plan. Copy it to make your own.")
        s = self.get_serializer(plan, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        return self._saved(s.save())


class PlanAssignmentViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Plans of one kind given to members. Trainers give them to their own members and admins to anyone; the desk sees
    its branches' and a member their own, with what's in the plan. Subclasses name the models and the audit word."""

    model = plans = None
    audit = ""
    roles = {"list": ALL, "retrieve": ALL, "*": COACHES}

    def get_queryset(self):
        qs = self.model.objects.filter(gym=self.gym).select_related("plan", "member", "assigned_by__user")
        role = self.me.role
        if role == GymRole.MEMBER:
            qs = qs.filter(member__user=self.request.user)
        elif role == GymRole.TRAINER:
            qs = qs.filter(member__trainer=self.me)
        else:
            qs = self.in_my_branches(qs, "member__home_branch")
        if (member := int_param(self.request, "member")) is not None:
            qs = qs.filter(member_id=member)
        if (plan := int_param(self.request, "plan")) is not None:
            qs = qs.filter(plan_id=plan)
        if self.request.query_params.get("current") == "true":
            qs = qs.filter(ended_at__isnull=True)
        return qs

    def members_i_coach(self):
        qs = Member.objects.filter(gym=self.gym, is_archived=False)
        return qs.filter(trainer=self.me) if self.me.role == GymRole.TRAINER else qs

    @extend_schema(request=AssignSerializer)
    def create(self, request, *args, **kwargs):
        """Give a member a plan. The one of this kind they're on now ends."""
        body = AssignSerializer(data=request.data, plans=self.plans.objects.filter(gym=self.gym), members=self.members_i_coach())
        body.is_valid(raise_exception=True)
        d = body.validated_data
        a = services.assign_plan(d["plan"], d["member"], by=self.me, note=d.get("note", ""))
        record(request, f"{self.audit}.assigned", a, None, {"member": a.member_id, "plan": a.plan_id})
        return Response(self.get_serializer(self.get_queryset().get(pk=a.pk)).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """Take a member off this plan, with nothing in its place."""
        a = services.end_plan(self.get_object(), by=self.me)
        record(request, f"{self.audit}.ended", a, {"ended_at": None}, {"ended_at": a.ended_at.isoformat()})
        return Response(self.get_serializer(self.get_queryset().get(pk=a.pk)).data)


@PLAN_FILTERS
class WorkoutPlanViewSet(CoachPlanViewSet):
    """The gym's workout plans: days, each with its exercises."""

    serializer_class = WorkoutPlanSerializer
    model, assignments = WorkoutPlan, WorkoutAssignment


@ASSIGNMENT_FILTERS
class WorkoutAssignmentViewSet(PlanAssignmentViewSet):
    """Workout plans given to members."""

    serializer_class = WorkoutAssignmentSerializer
    model, plans, audit = WorkoutAssignment, WorkoutPlan, "workout"


@PLAN_FILTERS
class DietPlanViewSet(CoachPlanViewSet):
    """The gym's diet plans: the day's targets, and each meal with what's in it."""

    serializer_class = DietPlanSerializer
    model, assignments = DietPlan, DietAssignment


@ASSIGNMENT_FILTERS
class DietAssignmentViewSet(PlanAssignmentViewSet):
    """Diet plans given to members."""

    serializer_class = DietAssignmentSerializer
    model, plans, audit = DietAssignment, DietPlan, "diet"
