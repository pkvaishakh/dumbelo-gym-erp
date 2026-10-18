from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.errors import RuleBroken
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, STAFF, GymViewMixin
from apps.gyms.models import GymRole
from apps.messages.notify import after_commit
from apps.messages.tasks import send_task_assigned

from .models import Task, TaskUpdate
from .services import overdue


class TaskUpdateSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.user.name", read_only=True)

    class Meta:
        model = TaskUpdate
        fields = ["id", "kind", "text", "author", "created_at"]
        read_only_fields = ["kind"]


class TaskSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(queryset=GymRole.objects.none())
    assignee_name = serializers.CharField(source="assignee.user.name", read_only=True)
    assignee_role = serializers.CharField(source="assignee.role", read_only=True)
    created_by_name = serializers.CharField(source="created_by.user.name", read_only=True)
    is_overdue = serializers.SerializerMethodField()
    updates = TaskUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "details", "assignee", "assignee_name", "assignee_role", "due_date", "due_time", "status", "is_overdue", "created_by_name", "created_at", "updates"]
        read_only_fields = ["status"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            self.fields["assignee"].queryset = GymRole.objects.filter(gym=req.gym, is_active=True, role__in=(GymRole.TRAINER, GymRole.RECEPTIONIST))

    def get_is_overdue(self, t) -> bool:
        return t.is_overdue()

    def create(self, data):
        req = self.context["request"]
        return Task.objects.create(gym=req.gym, created_by=req.gym_role, **data)


class DoneSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, help_text="A last update, posted before it's marked done")


NARROW = [
    OpenApiParameter("role", str, enum=["trainer", "receptionist"]), OpenApiParameter("assignee", int),
    OpenApiParameter("branch", int, description="Tasks of staff who work at this branch"),
    OpenApiParameter("q", str, description="Task title or details, or the assignee's name"),
]


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("state", str, enum=["open", "overdue", "done"]), *NARROW,
    OpenApiParameter("overdue", bool, description="Same as state=overdue"),
]))
class TaskViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Admins give trainers and receptionists tasks and track them. Staff see their own, start them, post updates
    and mark them done."""

    serializer_class = TaskSerializer
    roles = {"list": STAFF, "retrieve": STAFF, "start": STAFF, "done": STAFF, "reopen": STAFF, "updates": STAFF, "counts": STAFF, "*": ADMIN}
    filterset_fields = ["status", "due_date"]

    def _mine(self, by_role=True):
        """Tasks the caller may see (admins: all; staff: their own), narrowed by ?assignee=, ?branch= and ?q=,
        and by ?role= when by_role. The list and the counts share it, so the chips count what the list shows."""
        p = self.request.query_params
        qs = Task.objects.filter(gym=self.gym)
        if self.me.role != GymRole.ADMIN and self.me.role != "support":
            qs = qs.filter(assignee=self.me)
        if by_role and (role := p.get("role")) in GymRole.STAFF_ROLES:
            qs = qs.filter(assignee__role=role)
        if (assignee := int_param(self.request, "assignee")) is not None:
            qs = qs.filter(assignee_id=assignee)
        if (branch := int_param(self.request, "branch")) is not None:
            qs = qs.filter(assignee__branches=branch)
        if q := p.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(details__icontains=q) | Q(assignee__user__name__icontains=q))
        return qs

    def perform_create(self, serializer):
        task = serializer.save()
        after_commit(send_task_assigned, task.pk)  # tell them on WhatsApp, if the gym sends task messages

    def perform_update(self, serializer):
        before = serializer.instance.assignee_id
        task = serializer.save()
        if task.assignee_id != before:  # handed to someone else: they hear about it too
            after_commit(send_task_assigned, task.pk)

    def get_queryset(self):
        qs = self._mine().select_related("assignee__user", "created_by__user").prefetch_related("updates__author__user")
        state = self.request.query_params.get("state") or ("overdue" if self.request.query_params.get("overdue") == "true" else None)
        if state == "open":
            qs = qs.exclude(status=Task.DONE)
        elif state == "overdue":
            qs = qs.filter(overdue(self.gym))
        elif state == "done":
            qs = qs.filter(status=Task.DONE)
        # Open work first (by due date), finished work after it.
        done_last = Case(When(status=Task.DONE, then=Value(1)), default=Value(0), output_field=IntegerField())
        return qs.order_by(done_last, "due_date", "due_time", "id")

    @extend_schema(parameters=NARROW, responses=OpenApiTypes.OBJECT)
    @action(detail=False, methods=["get"])
    def counts(self, request):
        """How many tasks each filter chip holds: open, overdue, done and all for the filters, and all by role."""
        qs = self._mine()
        by_state = qs.aggregate(all=Count("id"), done=Count("id", filter=Q(status=Task.DONE)), overdue=Count("id", filter=overdue(self.gym)))
        by_state["open"] = by_state["all"] - by_state["done"]
        by_role = dict(self._mine(by_role=False).values_list("assignee__role").annotate(n=Count("id")))
        return Response({**by_state, "by_role": {"all": sum(by_role.values()), "trainer": by_role.get("trainer", 0), "receptionist": by_role.get("receptionist", 0)}})

    @transaction.atomic
    def _move(self, task, to, text):
        if task.status == to:
            raise RuleBroken("no_change", f"Already {task.get_status_display().lower()}")
        task.status = to
        task.save(update_fields=["status", "updated_at"])
        TaskUpdate.objects.create(task=task, author=self.me, kind=TaskUpdate.STATUS, text=text)
        return Response(self.get_serializer(Task.objects.prefetch_related("updates__author__user").get(pk=task.pk)).data)

    @extend_schema(request=None, responses=TaskSerializer)
    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        task = self.get_object()
        if task.status != Task.TODO:
            raise RuleBroken("bad_status", "Only a task that's to do can be started")
        return self._move(task, Task.DOING, "Started")

    @extend_schema(request=DoneSerializer, responses=TaskSerializer)
    @action(detail=True, methods=["post"])
    def done(self, request, pk=None):
        task = self.get_object()
        note = (request.data.get("note") or "").strip()
        if note:
            TaskUpdate.objects.create(task=task, author=self.me, text=note)
        return self._move(task, Task.DONE, "Marked done")

    @extend_schema(request=None, responses=TaskSerializer)
    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        task = self.get_object()
        if task.status != Task.DONE:
            raise RuleBroken("bad_status", "Only a finished task can be reopened")
        return self._move(task, Task.DOING if self.me.role != GymRole.ADMIN else Task.TODO, "Reopened")

    @extend_schema(request=TaskUpdateSerializer, responses={201: TaskUpdateSerializer})
    @action(detail=True, methods=["post"])
    def updates(self, request, pk=None):
        """Post an update on progress."""
        task = self.get_object()
        s = TaskUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(task=task, author=self.me, kind=TaskUpdate.NOTE)
        return Response(s.data, status=201)
