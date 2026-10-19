"""The Console's Home (`/api/platform/summary/`), gyms and their admin accounts (`/api/platform/gyms/`,
`/api/platform/gyms/<id>/admins/`), and its Server screen (`/api/platform/status/`, `/api/platform/jobs/<job>/run/`).

Dumbelo admins only (`DumbeloViewMixin`), with no X-Gym: these views work across gyms. They never show what is
inside a gym (members' details, payments, check-ins): only counts, branches and admin accounts. Every change is
audited against the gym it belongs to.
"""
from django.db.models import OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.queries import count_of
from apps.core.dumbelo import DumbeloViewMixin
from apps.gyms.models import Gym, GymRole
from apps.gyms.serializers import StaffPasswordSerializer

from . import server, services, summary
from .queries import GymFilter, gyms, with_branches
from .serializers import (
    GymAdminAddSerializer, GymAdminSerializer, GymCreateSerializer, GymDetailSerializer, GymEditSerializer, GymRowSerializer,
    JobRunSerializer, NewGymSerializer, PlatformSummarySerializer, ServerStatusSerializer, StatusChangeSerializer,
)


def _audit_status(gym):
    return {"status": gym.status, "reason": gym.status_reason}


@extend_schema(tags=["platform"])
class GymViewSet(DumbeloViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                 mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Every gym on Dumbelo. Gyms are never deleted: a gym that stops paying is suspended."""

    filterset_class = GymFilter
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        qs = gyms().order_by("name")
        if self.action == "retrieve":
            qs = with_branches(qs)
        text = self.request.query_params.get("q", "").strip()
        if self.action == "list" and len(text) >= 2:
            qs = qs.filter(Q(name__icontains=text) | Q(slug__icontains=text))
        return qs

    def get_serializer_class(self):
        return {"retrieve": GymDetailSerializer, "create": GymCreateSerializer, "partial_update": GymEditSerializer}.get(self.action, GymRowSerializer)

    def _detail(self, gym, **extra):
        """The gym as its screen shows it, read again after a change."""
        gym = with_branches(gyms()).get(pk=gym.pk)
        for k, v in extra.items():
            setattr(gym, k, v)
        return gym

    @extend_schema(parameters=[OpenApiParameter("q", str, description="Name or short name, 2 characters or more")])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=GymCreateSerializer, responses={201: NewGymSerializer})
    def create(self, request, *args, **kwargs):
        """New Gym: on trial, with its first branch and its owner admin, who can sign in at once."""
        s = GymCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        made = services.create_gym(
            name=v["name"], slug=v["slug"], timezone_name=v["timezone"], branch=v["branch"], owner_email=v["owner_email"],
            owner_name=v.get("owner_name", ""), owner_password=v.get("owner_password") or None, billing_email=v.get("billing_email", ""),
        )
        record(request, "gym.created", made.gym, None, {"slug": made.gym.slug, "owner": made.owner.user.email, "new_login": made.new_login}, gym=made.gym)
        return Response(NewGymSerializer(self._detail(made.gym, owner_new_login=made.new_login)).data, status=201)

    @extend_schema(request=GymEditSerializer, responses=GymDetailSerializer)
    def partial_update(self, request, *args, **kwargs):
        """Change the gym's name, time zone or billing email. The short name never changes: the app sends it."""
        gym = self.get_object()
        fields = ["name", "timezone", "billing_email"]
        before = {f: getattr(gym, f) for f in fields}
        s = GymEditSerializer(gym, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        after = {f: getattr(gym, f) for f in fields}
        if before != after:
            record(request, "gym.changed", gym, before, after, gym=gym)
        return Response(GymDetailSerializer(self._detail(gym)).data)

    def _status(self, request, change, what):
        gym = self.get_object()
        s = StatusChangeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = _audit_status(gym)
        gym = change(gym, s.validated_data["reason"])
        record(request, what, gym, before, _audit_status(gym), gym=gym)
        return Response(GymDetailSerializer(self._detail(gym)).data)

    @extend_schema(request=StatusChangeSerializer, responses=GymDetailSerializer)
    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        """Pause the gym: staff and members are refused at once, admins keep their Dumbelo plan, messages stop."""
        return self._status(request, services.suspend, "gym.suspended")

    @extend_schema(request=StatusChangeSerializer, responses=GymDetailSerializer)
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Turn a suspended or trial gym on."""
        return self._status(request, services.activate, "gym.activated")


@extend_schema(tags=["platform"], parameters=[OpenApiParameter("gym_id", int, OpenApiParameter.PATH, description="The gym's id")])
class GymAdminViewSet(DumbeloViewMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """A gym's admin accounts: Add Admin, Reset Password, Deactivate (never the owner), Reactivate, Make Owner."""

    serializer_class = GymAdminSerializer
    pagination_class = None  # a gym has a handful of admins: the screen shows them all

    @property
    def gym(self):
        if getattr(self, "swagger_fake_view", False):
            return None
        if not hasattr(self, "_gym"):
            self._gym = get_object_or_404(Gym, pk=self.kwargs["gym_id"])
        return self._gym

    def get_queryset(self):
        others = GymRole.objects.filter(user=OuterRef("user"), is_active=True).exclude(gym=OuterRef("gym"))
        return (GymRole.objects.filter(gym=self.gym, role=GymRole.ADMIN).select_related("user")
                .annotate(other_gyms=count_of(others)).order_by("-is_owner", "-is_active", "user__name"))

    def _row(self, role):
        return GymAdminSerializer(self.get_queryset().get(pk=role.pk)).data

    @extend_schema(request=GymAdminAddSerializer, responses={201: GymAdminSerializer})
    def create(self, request, *args, **kwargs):
        """Add Admin: someone new to Dumbelo gets a login with the first password you set; someone who already
        signs in (at another gym) keeps theirs. A deactivated admin is turned back on."""
        s = GymAdminAddSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        role, new = services.add_admin(self.gym, email=v["email"], name=v.get("name", ""), password=v.get("password") or None)
        record(request, "admin.added", role, None, {"email": role.user.email, "new_login": new}, gym=self.gym)
        return Response(self._row(role), status=201)

    @extend_schema(request=StaffPasswordSerializer, responses={204: None})
    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, gym_id=None, pk=None):
        """A new password for an admin who lost theirs. They're signed out on every device."""
        role = self.get_object()
        s = StaffPasswordSerializer(data=request.data, context={"request": request, "user": role.user})
        s.is_valid(raise_exception=True)
        services.reset_admin_password(role, s.validated_data["password"])
        record(request, "admin.password_reset", role, gym=self.gym)
        return Response(status=204)

    @extend_schema(request=None, responses=GymAdminSerializer)
    @action(detail=True, methods=["post"])
    def deactivate(self, request, gym_id=None, pk=None):
        role = services.deactivate_admin(self.get_object())
        record(request, "admin.deactivated", role, {"is_active": True}, {"is_active": False}, gym=self.gym)
        return Response(self._row(role))

    @extend_schema(request=None, responses=GymAdminSerializer)
    @action(detail=True, methods=["post"])
    def reactivate(self, request, gym_id=None, pk=None):
        role = services.reactivate_admin(self.get_object())
        record(request, "admin.reactivated", role, {"is_active": False}, {"is_active": True}, gym=self.gym)
        return Response(self._row(role))

    @extend_schema(request=None, responses=GymAdminSerializer)
    @action(detail=True, methods=["post"], url_path="make-owner")
    def make_owner(self, request, gym_id=None, pk=None):
        """Make this admin the account owner: they handle Dumbelo billing. The old owner stays an admin."""
        role = self.get_object()
        before = services.make_owner(role)
        record(request, "admin.made_owner", role, {"owner": before.user.email if before else None}, {"owner": role.user.email}, gym=self.gym)
        return Response(self._row(role))


@extend_schema(tags=["platform"])
class PlatformSummaryView(DumbeloViewMixin, APIView):
    """Console → Home: gyms by status, what they owe Dumbelo, branch requests waiting, today's WhatsApp messages
    and the shared number's month, and what on the server is down or failed. A fixed number of queries."""

    @extend_schema(responses=PlatformSummarySerializer)
    def get(self, request):
        return Response(PlatformSummarySerializer(summary.summary()).data)


@extend_schema(tags=["platform"])
class ServerStatusView(DumbeloViewMixin, APIView):
    """Console → Server: the version running, whether the database, Redis, the worker and beat answer, each job's
    last run, messages waiting or failed, and Meta's webhook calls. Something down shows as down, never as a 500."""

    @extend_schema(responses=ServerStatusSerializer)
    def get(self, request):
        return Response(ServerStatusSerializer(server.status()).data)


@extend_schema(tags=["platform"], parameters=[
    OpenApiParameter("job", str, OpenApiParameter.PATH, enum=[j for j, spec in server.JOBS.items() if spec.task])])
class JobRunNowView(DumbeloViewMixin, APIView):
    @extend_schema(request=None, responses={202: JobRunSerializer})
    def post(self, request, job):
        """Run Now: queue one run of reminders, invoices or the webhook replay on the worker. They are safe to
        repeat; refused while that job is waiting or running. Audited."""
        if job not in server.JOBS or server.JOBS[job].task is None:
            raise Http404
        run = server.run_now(job, request.user)
        record(request, "job.run_now", run, None, {"job": job})
        return Response(JobRunSerializer(run).data, status=status.HTTP_202_ACCEPTED)
