from django.db.models import Count
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field, extend_schema_view
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from apps.audit.models import record
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.params import int_param, open_days
from apps.core.tenancy import ADMIN, ALL, DESK, GymViewMixin
from apps.gyms.models import Branch, GymRole
from apps.members.models import Member
from apps.members.serializers import GymPK, gym_of

from .models import CheckIn, Device
from .services import check_in, count_by_session, deactivate_device, rotate_device_token, session_name


class CheckInSerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    person_id = serializers.SerializerMethodField()
    code = serializers.CharField(source="member.code", default=None)
    branch_name = serializers.CharField(source="branch.name")
    time = serializers.SerializerMethodField()
    session = serializers.SerializerMethodField()

    class Meta:
        model = CheckIn
        fields = ["id", "kind", "person_id", "name", "code", "branch", "branch_name", "at", "local_date", "time", "session", "source"]

    @extend_schema_field(serializers.ChoiceField(["member", "admin", "receptionist", "trainer"]))
    def get_kind(self, c):
        return "member" if c.member_id else c.staff.role

    def get_name(self, c) -> str:
        return c.member.name if c.member_id else c.staff.user.name

    def get_person_id(self, c) -> int:
        return c.member_id or c.staff_id

    def get_time(self, c) -> str:
        return clock.time_label(c.gym, c.at)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_session(self, c):
        return session_name(c, c.gym)


class CheckInCreateSerializer(serializers.Serializer):
    branch = serializers.IntegerField()
    member = serializers.IntegerField(required=False)
    staff = serializers.IntegerField(required=False)

    def validate(self, data):
        if ("member" in data) == ("staff" in data):
            raise serializers.ValidationError("Check in a member or a staff member")
        return data


class CheckInViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Who came in. Only the time in is recorded — there is no check-out.

    The desk checks people in; staff see their branches' list; a member sees their own visits; admins can remove
    a mistaken check-in (audited)."""

    serializer_class = CheckInSerializer
    roles = {"list": ALL, "summary": ("admin", "receptionist", "trainer"), "destroy": ADMIN, "*": DESK}

    def get_queryset(self):
        qs = CheckIn.objects.filter(gym=self.gym).select_related("gym", "member", "staff__user", "branch").prefetch_related("branch__sessions")
        if self.me.role == GymRole.MEMBER:
            return qs.filter(member__user=self.request.user)
        qs = self.in_my_branches(qs)
        if self.action == "destroy":
            return qs
        p = self.request.query_params
        member, staff = int_param(self.request, "member"), int_param(self.request, "staff")
        if member is not None or staff is not None:  # one person's visits, any day or between two (member, staff profile)
            qs = qs.filter(member_id=member) if member is not None else qs.filter(staff_id=staff)
            first, last = open_days(self.request)
            if first:
                qs = qs.filter(local_date__gte=first)
            if last:
                qs = qs.filter(local_date__lte=last)
            return qs
        day = clock.parse_date(p.get("date"), clock.today(self.gym))
        qs = qs.filter(local_date=day)
        if (branch := int_param(self.request, "branch")) is not None:
            qs = qs.filter(branch_id=branch)
        kind = p.get("kind")  # member | staff | trainer | receptionist | admin
        if kind == "member":
            qs = qs.filter(member__isnull=False)
        elif kind == "staff":
            qs = qs.filter(staff__isnull=False)
        elif kind in GymRole.STAFF_ROLES:
            qs = qs.filter(staff__role=kind)
        if p.get("source"):
            qs = qs.filter(source=p["source"])
        if p.get("q"):
            q = p["q"]
            qs = qs.filter(member__name__icontains=q) | qs.filter(staff__user__name__icontains=q) | qs.filter(member__code__icontains=q)
        return qs

    @extend_schema(parameters=[
        OpenApiParameter("date", str, description="YYYY-MM-DD, today by default"), OpenApiParameter("branch", int),
        OpenApiParameter("kind", str, enum=["member", "staff", "trainer", "receptionist", "admin"]),
        OpenApiParameter("session", str, description="Session name, e.g. Morning; Other for outside every session"), OpenApiParameter("source", str), OpenApiParameter("q", str),
        OpenApiParameter("member", int, description="One member's visits, any day"), OpenApiParameter("staff", int),
        OpenApiParameter("from", str, description="With member or staff: YYYY-MM-DD, the first day"),
        OpenApiParameter("to", str, description="With member or staff: YYYY-MM-DD, the last day"),
    ])
    def list(self, request, *args, **kwargs):
        session = request.query_params.get("session")
        if not session:
            return super().list(request, *args, **kwargs)
        rows = [c for c in self.get_queryset() if (session_name(c, self.gym) or "Other").lower() == session.lower()]
        page = self.paginate_queryset(rows)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @extend_schema(request=CheckInCreateSerializer, responses={201: CheckInSerializer})
    def create(self, request, *args, **kwargs):
        s = CheckInCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        branch = self.in_my_branches(Branch.objects.filter(gym=self.gym), "id").filter(pk=d["branch"]).first()
        if branch is None:
            raise RuleBroken("wrong_branch", "You don't work at this branch")
        if "member" in d:
            member = Member.objects.filter(gym=self.gym, pk=d["member"]).first()
            if member is None:
                raise RuleBroken("not_found", "No such member")
            c = check_in(branch, member=member, source=CheckIn.DESK, by=request.user)
        else:
            staff = GymRole.objects.filter(gym=self.gym, pk=d["staff"]).select_related("user").first()
            if staff is None:
                raise RuleBroken("not_found", "No such staff member")
            c = check_in(branch, staff=staff, source=CheckIn.DESK, by=request.user)
        return Response(self.get_serializer(c).data, status=201)

    def perform_destroy(self, c):
        record(self.request, "checkin.removed", c, {"at": c.at.isoformat(), "member": c.member_id, "staff": c.staff_id})
        c.delete()

    @extend_schema(parameters=[OpenApiParameter("date", str), OpenApiParameter("branch", int)])
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Counts for the day by session: members, trainers, receptionists — the Attendance and Home cards.

        Without a branch, `branches` also gives each of your branches' member check-ins by source."""
        qs = self.get_queryset()
        totals, sessions = count_by_session(qs, self.gym)
        members = qs.filter(member__isnull=False)
        sources = {s: 0 for s, _ in CheckIn.SOURCES}
        sources.update(members.values_list("source").annotate(n=Count("id")))
        out = {"totals": totals, "sessions": sessions, "member_sources": sources}
        if int_param(request, "branch") is None and self.me.role != GymRole.MEMBER:
            per = {}
            for b, src, n in members.order_by().values_list("branch_id", "source").annotate(n=Count("id")):
                per.setdefault(b, {s: 0 for s, _ in CheckIn.SOURCES})[src] = n
            mine = self.in_my_branches(Branch.objects.filter(gym=self.gym, is_active=True), "id").order_by("name")
            zero = {s: 0 for s, _ in CheckIn.SOURCES}
            out["branches"] = [
                {"id": b.id, "name": b.name, "member": sum(per.get(b.id, zero).values()), "member_sources": per.get(b.id, zero)}
                for b in mine
            ]
        return Response(out)


class QRSerializer(serializers.Serializer):
    code = serializers.CharField(help_text="The code printed on the branch's wall QR")


class QRCheckInView(APIView):
    """A signed-in member or staff member scans the branch's wall QR with their phone."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "qr"

    @extend_schema(request=QRSerializer, responses={201: CheckInSerializer})
    def post(self, request):
        s = QRSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        branch = Branch.objects.select_related("gym").filter(qr_code=s.validated_data["code"]).first()
        if branch is None:
            raise RuleBroken("bad_qr", "This QR code isn't a Dumbelo check-in code")
        role = GymRole.objects.filter(user=request.user, gym=branch.gym, is_active=True).first()
        if role is None:
            raise RuleBroken("not_in_gym", f"You're not a member of {branch.gym.name}")
        if role.role == GymRole.MEMBER:
            member = Member.objects.filter(gym=branch.gym, user=request.user).first()
            if member is None:
                raise RuleBroken("not_in_gym", "Ask the desk to link your membership")
            c = check_in(branch, member=member, source=CheckIn.QR, by=request.user)
        else:
            c = check_in(branch, staff=role, source=CheckIn.QR, by=request.user)
        return Response(CheckInSerializer(c).data, status=201)


class PunchSerializer(serializers.Serializer):
    user_id = serializers.CharField(help_text="The person's number on the device")
    at = serializers.DateTimeField(required=False, help_text="When they punched; now if missing")


class DevicePunchView(APIView):
    """A turnstile or biometric reader posts each punch here with its token in X-Device-Token.

    Answers {"open": true} to let them through. A second punch the same day is fine (open, not recorded again);
    an ended or frozen plan answers open: false with the reason so the device can show it."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "device"

    @extend_schema(request=PunchSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        token = request.headers.get("X-Device-Token", "")
        device = Device.objects.select_related("branch__gym").filter(token=token, is_active=True).first() if token else None
        if device is None:
            return Response({"error": {"code": "bad_device", "message": "Unknown device"}}, status=401)
        device.last_seen = timezone.now()
        device.save(update_fields=["last_seen"])
        s = PunchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        uid, at = s.validated_data["user_id"], s.validated_data.get("at")
        gym = device.branch.gym
        member = Member.objects.filter(gym=gym, device_user_id=uid).first()
        staff = None if member else GymRole.objects.filter(gym=gym, device_user_id=uid, is_active=True).select_related("user").first()
        if member is None and staff is None:
            return Response({"open": False, "code": "unknown_person", "message": "Not registered"})
        try:
            c = check_in(device.branch, member=member, staff=staff, source=CheckIn.DEVICE, at=at)
        except RuleBroken as e:
            if e.rule_code == "already_checked_in":
                return Response({"open": True, "recorded": False, "message": str(e.detail)})
            return Response({"open": False, "code": e.rule_code, "message": str(e.detail)})
        return Response({"open": True, "recorded": True, "checkin": c.id})


class DeviceSerializer(serializers.ModelSerializer):
    """A device as the Devices screen shows it. Never the token: that is shown once and then only on the device."""

    branch = GymPK(Branch)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Device
        fields = ["id", "branch", "branch_name", "name", "serial", "is_active", "last_seen"]
        read_only_fields = ["is_active", "last_seen"]

    def validate_serial(self, serial):
        serial = serial.strip()
        clash = Device.objects.filter(gym=gym_of(self.context), serial__iexact=serial)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():  # the same number twice in one gym means it was typed wrong
            raise serializers.ValidationError("You already have a device with this serial number")
        return serial


class DeviceWithTokenSerializer(DeviceSerializer):
    """The answer to adding a device or rotating its token: the one time the token is sent back."""

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + ["token"]
        read_only_fields = DeviceSerializer.Meta.read_only_fields + ["token"]


class DeviceEditSerializer(DeviceSerializer):
    """Renaming a device or moving it to another branch. The serial belongs to the hardware, so it stays."""

    class Meta(DeviceSerializer.Meta):
        read_only_fields = DeviceSerializer.Meta.read_only_fields + ["serial"]


@extend_schema_view(
    list=extend_schema(parameters=[OpenApiParameter("branch", int, description="Only this branch's devices")]),
    create=extend_schema(request=DeviceSerializer, responses={201: DeviceWithTokenSerializer}),
)
class DeviceViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """The turnstiles and biometric readers that post to /api/devices/punch/. Admins only.

    Adding a device or rotating its token answers with the token; it is never listed again, so it has to be
    copied onto the device there and then. A device that has gone is switched off, never deleted: its punches
    stay part of the gym's history."""

    roles = {"*": ADMIN}
    filterset_fields = ["branch"]

    def get_serializer_class(self):
        if self.action == "create":
            return DeviceWithTokenSerializer
        if self.action in ("update", "partial_update"):
            return DeviceEditSerializer
        return DeviceSerializer

    def get_queryset(self):
        qs = Device.objects.filter(gym=self.gym).select_related("branch")
        return self.in_my_branches(qs, "branch").order_by("branch__name", "name")

    def perform_create(self, serializer):
        device = serializer.save()
        record(self.request, "device.added", device, None, {"name": device.name, "serial": device.serial, "branch": device.branch_id})

    @extend_schema(request=None, responses=DeviceSerializer)
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Switch a device off. Its token stops working at the door straight away."""
        device = deactivate_device(self.get_object())
        record(request, "device.deactivated", device, {"is_active": True}, {"is_active": False})
        return Response(DeviceSerializer(device, context=self.get_serializer_context()).data)

    @extend_schema(request=None, responses=DeviceWithTokenSerializer)
    @action(detail=True, methods=["post"], url_path="rotate-token")
    def rotate(self, request, pk=None):
        """Give the device a new token, for a reader that was replaced or a token that got out."""
        device = rotate_device_token(self.get_object())
        record(request, "device.token_rotated", device)  # the token itself is never audited
        return Response(DeviceWithTokenSerializer(device, context=self.get_serializer_context()).data)
