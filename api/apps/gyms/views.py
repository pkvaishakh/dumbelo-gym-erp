from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import reset_staff_password
from apps.audit.models import record
from apps.core.errors import RuleBroken
from apps.core.tenancy import ADMIN, ALL, STAFF, GymViewMixin

from .models import Branch, GymRole, SupportAccess
from .serializers import BranchSerializer, GymSettingsSerializer, StaffPasswordSerializer, StaffSerializer, SupportAccessSerializer


class BranchViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Branches and their opening sessions. Admins change them; everyone sees the branches they belong to."""

    serializer_class = BranchSerializer
    roles = {"list": ALL, "retrieve": ALL, "*": ADMIN}

    def get_queryset(self):
        qs = Branch.objects.filter(gym=self.gym).prefetch_related("sessions")
        ids = self.me.branch_ids()
        return qs if ids is None else qs.filter(id__in=ids)

    def perform_destroy(self, branch):
        if branch.members.exists() or branch.checkins.exists() or branch.cash_accounts.exists():
            raise ValidationError("This branch has members or history. Mark it inactive instead.")
        branch.delete()


class StaffViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Admins, receptionists and trainers of the gym. Only admins manage staff; staff can read the list."""

    serializer_class = StaffSerializer
    roles = {"list": STAFF, "retrieve": STAFF, "*": ADMIN}
    filterset_fields = ["role", "is_active", "branches"]

    def get_queryset(self):
        return GymRole.objects.filter(gym=self.gym, role__in=GymRole.STAFF_ROLES).select_related("user").prefetch_related("branches").order_by("role", "user__name")

    def perform_update(self, serializer):
        before = {"role": serializer.instance.role, "is_active": serializer.instance.is_active}
        role = serializer.save()
        after = {"role": role.role, "is_active": role.is_active}
        if before != after:
            record(self.request, "staff.changed", role, before, after)

    @extend_schema(request=StaffPasswordSerializer, responses={204: None})
    @action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        """Give a receptionist or trainer a new password (they forgot theirs). They're signed out everywhere."""
        role = self.get_object()
        data = StaffPasswordSerializer(data=request.data, context={"request": request, "user": role.user})
        data.is_valid(raise_exception=True)
        reset_staff_password(role, data.validated_data["password"])
        record(request, "staff.password_reset", role)
        return Response(status=204)

    def perform_destroy(self, role):
        if role.is_owner:
            raise ValidationError("The account owner can't be removed")
        record(self.request, "staff.deactivated", role, {"is_active": True}, {"is_active": False})
        role.is_active = False  # people keep their history: deactivate, never delete
        role.save()


class SupportAccessViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """An admin lets Rackline support look inside the gym for a few hours, and can take it back at any time.

    A window is only ever read-only (see `InGym`), one gym at a time, and both the granting and the ending are
    written to the audit log. Windows are never deleted: ending one moves its end to now, so the history keeps
    what really happened."""

    serializer_class = SupportAccessSerializer
    roles = {"*": ADMIN}

    def get_queryset(self):
        return SupportAccess.objects.filter(gym=self.gym).select_related("granted_by")

    def perform_create(self, serializer):
        window = serializer.save()
        record(self.request, "support.granted", window, None, {"starts": window.starts.isoformat(), "ends": window.ends.isoformat()})

    @extend_schema(request=None, responses=SupportAccessSerializer)
    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """Take the access back now. Rackline loses the gym on its next call."""
        window = self.get_object()
        now = timezone.now()
        if window.ends <= now:
            raise RuleBroken("not_open", "This access has already ended")
        before = {"ends": window.ends.isoformat()}
        window.ends = now
        window.save(update_fields=["ends", "updated_at"])
        record(request, "support.ended", window, before, {"ends": window.ends.isoformat()})
        return Response(self.get_serializer(window).data)


class GymSettingsView(GymViewMixin, APIView):
    """The gym as Rackline set it up (name, slug, time zone), for More → Settings. Admins only. Nothing here
    changes: the gym's message switches are `/api/gym/messages/`."""

    roles = {"*": ADMIN}

    @extend_schema(responses=GymSettingsSerializer)
    def get(self, request):
        return Response(GymSettingsSerializer(self.gym).data)
