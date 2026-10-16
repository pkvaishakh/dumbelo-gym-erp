import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.core.errors import RuleBroken

from .models import Branch, BranchSession, GymRole, SupportAccess

User = get_user_model()


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchSession
        fields = ["id", "name", "starts", "ends"]
        read_only_fields = ["id"]


class BranchSerializer(serializers.ModelSerializer):
    """A branch with its opening sessions. Sending `sessions` replaces the whole list (as the Edit Branch form does)."""

    sessions = SessionSerializer(many=True)

    class Meta:
        model = Branch
        fields = ["id", "name", "address", "phone", "days_open", "sessions", "qr_code", "is_active"]
        read_only_fields = ["id", "qr_code"]

    def validate_sessions(self, rows):
        if not rows:
            raise serializers.ValidationError("Add at least one session")
        names = set()
        for r in rows:
            n = r["name"].strip()
            if not n:
                raise serializers.ValidationError("Name every session")
            if n.lower() in names:
                raise serializers.ValidationError(f"There is already a session called {n}")
            names.add(n.lower())
            if r["ends"] <= r["starts"]:
                raise serializers.ValidationError(f"{n} must end after it starts")
        rows = sorted(rows, key=lambda r: r["starts"])
        for a, b in zip(rows, rows[1:]):
            if b["starts"] < a["ends"]:
                raise serializers.ValidationError(f"{b['name']} overlaps {a['name']}")
        return rows

    def validate_name(self, value):
        gym = self.context["request"].gym
        clash = Branch.objects.filter(gym=gym, name__iexact=value.strip())
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError(f"There is already a branch called {value.strip()}")
        return value.strip()

    @transaction.atomic
    def create(self, data):
        sessions = data.pop("sessions")
        branch = Branch.objects.create(gym=self.context["request"].gym, **data)
        BranchSession.objects.bulk_create([BranchSession(branch=branch, **s) for s in sessions])
        return branch

    @transaction.atomic
    def update(self, branch, data):
        sessions = data.pop("sessions", None)
        for k, v in data.items():
            setattr(branch, k, v)
        branch.save()
        if sessions is not None:
            branch.sessions.all().delete()
            BranchSession.objects.bulk_create([BranchSession(branch=branch, **s) for s in sessions])
        return branch


class StaffSerializer(serializers.ModelSerializer):
    """A trainer, receptionist or admin. Creating one creates their login (email + a first password they change)."""

    name = serializers.CharField(source="user.name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField(source="user.phone", required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    branches = serializers.PrimaryKeyRelatedField(many=True, queryset=Branch.objects.none())

    class Meta:
        model = GymRole
        fields = ["id", "name", "email", "phone", "password", "role", "branches", "is_owner", "is_active", "shift", "specialities", "day_off", "device_user_id"]
        read_only_fields = ["id", "is_owner"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            self.fields["branches"].child_relation.queryset = Branch.objects.filter(gym=req.gym)

    def validate_role(self, value):
        if value not in GymRole.STAFF_ROLES:
            raise serializers.ValidationError("Staff are admins, receptionists or trainers")
        return value

    def validate(self, data):
        role = data.get("role", getattr(self.instance, "role", None))
        branches = data.get("branches", None)
        if role != GymRole.ADMIN and branches is not None and not branches:
            raise serializers.ValidationError({"branches": "Choose at least one branch"})
        if self.instance and self.instance.is_owner and (data.get("role", GymRole.ADMIN) != GymRole.ADMIN or data.get("is_active") is False):
            raise serializers.ValidationError("The account owner stays an active admin")
        return data

    @transaction.atomic
    def create(self, data):
        gym = self.context["request"].gym
        u = data.pop("user")
        password = data.pop("password", None) or secrets.token_urlsafe(12)
        user = User.objects.filter(email__iexact=u["email"]).first()
        if user is None:
            user = User.objects.create_user(email=u["email"], password=password, name=u["name"], phone=u.get("phone") or None)
        elif GymRole.objects.filter(user=user, gym=gym).exists():
            raise serializers.ValidationError({"email": "This person already has a role in this gym"})
        branches = data.pop("branches", [])
        role = GymRole.objects.create(user=user, gym=gym, **data)
        role.branches.set(branches)
        return role

    @transaction.atomic
    def update(self, role, data):
        u = data.pop("user", {})
        data.pop("password", None)
        for k, v in u.items():
            setattr(role.user, k, v or None if k == "phone" else v)
        role.user.save()
        branches = data.pop("branches", None)
        for k, v in data.items():
            setattr(role, k, v)
        role.save()
        if branches is not None:
            role.branches.set(branches)
        return role


class SupportAccessSerializer(serializers.ModelSerializer):
    """A window an admin opened for Rackline support. `open` says whether it is running right now."""

    hours = serializers.IntegerField(write_only=True, min_value=1, max_value=72, help_text="How long Rackline support may look")
    granted_by_name = serializers.CharField(source="granted_by.name", read_only=True)
    open = serializers.SerializerMethodField()

    class Meta:
        model = SupportAccess
        fields = ["id", "starts", "ends", "hours", "granted_by", "granted_by_name", "open"]
        read_only_fields = ["id", "starts", "ends", "granted_by"]

    def get_open(self, window) -> bool:
        return window.starts <= timezone.now() < window.ends

    def create(self, data):
        req = self.context["request"]
        now = timezone.now()
        if SupportAccess.open_for(req.gym):
            raise RuleBroken("already_open", "Rackline already has access. End it first to change how long it lasts.")
        return SupportAccess.objects.create(gym=req.gym, granted_by=req.user, starts=now, ends=now + timedelta(hours=data["hours"]))
