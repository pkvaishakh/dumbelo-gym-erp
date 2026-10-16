from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from apps.audit.models import record
from apps.core.tenancy import ADMIN, ALL, STAFF, GymViewMixin

from .models import Branch, GymRole, SupportAccess
from .serializers import BranchSerializer, StaffSerializer, SupportAccessSerializer


class BranchViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Branches and their opening sessions. Admins change them; everyone sees the branches they belong to."""

    serializer_class = BranchSerializer
    roles = {"list": ALL, "retrieve": ALL, "*": ADMIN}

    def get_queryset(self):
        qs = Branch.objects.filter(gym=self.gym).prefetch_related("sessions")
        ids = self.me.branch_ids()
        return qs if ids is None else qs.filter(id__in=ids)

    def perform_destroy(self, branch):
        if branch.members.exists() or branch.checkins.exists():
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

    def perform_destroy(self, role):
        if role.is_owner:
            raise ValidationError("The account owner can't be removed")
        record(self.request, "staff.deactivated", role, {"is_active": True}, {"is_active": False})
        role.is_active = False  # people keep their history: deactivate, never delete
        role.save()


class SupportAccessViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """An admin lets Rackline support look inside the gym for a few hours."""

    serializer_class = SupportAccessSerializer
    roles = {"*": ADMIN}

    def get_queryset(self):
        return SupportAccess.objects.filter(gym=self.gym)
