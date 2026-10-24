import secrets
from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts import usernames
from apps.accounts.models import normalize_email, normalize_phone
from apps.accounts.services import check_login_is_this_gyms, check_no_role_here, find_by_username, new_login
from apps.billing.services import make_room_for_branch
from apps.core.errors import RuleBroken

from .models import Branch, BranchSession, Gym, GymRole, SupportAccess


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
        gym = self.context["request"].gym
        if data.get("is_active", True):
            make_room_for_branch(gym)
        branch = Branch.objects.create(gym=gym, **data)
        BranchSession.objects.bulk_create([BranchSession(branch=branch, **s) for s in sessions])
        return branch

    @transaction.atomic
    def update(self, branch, data):
        sessions = data.pop("sessions", None)
        if data.get("is_active") and not branch.is_active:  # reopening takes a place in the plan again
            make_room_for_branch(branch.gym, branch)
        for k, v in data.items():
            setattr(branch, k, v)
        branch.save()
        if sessions is not None:
            branch.sessions.all().delete()
            BranchSession.objects.bulk_create([BranchSession(branch=branch, **s) for s in sessions])
        return branch


class GymSettingsSerializer(serializers.ModelSerializer):
    """The gym as Dumbelo set it up (name, slug, time zone), and how long its plans' months run, which its admins
    set. Its message switches are /api/gym/messages/."""

    MAX_MONTH_DAYS = 60

    class Meta:
        model = Gym
        fields = ["name", "slug", "timezone", "month_days"]
        read_only_fields = ["name", "slug", "timezone"]

    def validate_month_days(self, n):
        if n > self.MAX_MONTH_DAYS:
            raise serializers.ValidationError(f"Use 1 to {self.MAX_MONTH_DAYS} days, or calendar months")
        return n


def _same_form(field, value):
    """A sent username, name, email or phone in the form it's stored in, so resending an unchanged value isn't an edit."""
    if field == "phone":
        try:
            return normalize_phone(value)
        except DjangoValidationError:
            return value
    if field == "email":
        return normalize_email(value)
    if field == "username":
        return usernames.clean(value)
    return value


class StaffSerializer(serializers.ModelSerializer):
    """A trainer, receptionist or admin. Adding one makes their login (a username and a first password they change),
    or, with `existing_username`, adds someone who already signs in to Dumbelo as they are: their password, name
    and details stay theirs."""

    username = serializers.CharField(source="user.username", required=False, allow_blank=True, max_length=60,
                                     help_text="How they sign in. Left out on Add Staff, one is made from the email or name")
    existing_username = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=60,
                                              help_text="Add someone who already signs in to Dumbelo (at another gym) by their username")
    name = serializers.CharField(source="user.name", max_length=120, error_messages={"required": "Enter their name", "blank": "Enter their name"})
    email = serializers.EmailField(source="user.email", required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(source="user.phone", required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    branches = serializers.PrimaryKeyRelatedField(many=True, queryset=Branch.objects.none())

    class Meta:
        model = GymRole
        fields = ["id", "username", "existing_username", "name", "email", "phone", "password", "role", "branches", "is_owner", "is_active", "shift", "specialities", "day_off", "device_user_id"]
        read_only_fields = ["id", "is_owner"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            self.fields["branches"].child_relation.queryset = Branch.objects.filter(gym=req.gym)
        data = kwargs.get("data")
        if self.instance is not None or (hasattr(data, "get") and data.get("existing_username")):
            self.fields["name"].required = False  # an edit, or someone who brings their own login, name and all

    def validate_role(self, value):
        if value not in GymRole.STAFF_ROLES:
            raise serializers.ValidationError("Staff are admins, receptionists or trainers")
        return value

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_email(self, value):
        return normalize_email(value)

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
        u = data.pop("user", {})
        password = data.pop("password", None) or secrets.token_urlsafe(12)
        existing = data.pop("existing_username", "")
        if existing:
            user = find_by_username(existing)
            check_no_role_here(user, gym)
        else:
            user = new_login(username=u.get("username"), password=password, name=u["name"].strip(), email=u.get("email"), phone=u.get("phone"))
        branches = data.pop("branches", [])
        role = GymRole.objects.create(user=user, gym=gym, **data)
        role.branches.set(branches)
        return role

    @transaction.atomic
    def update(self, role, data):
        u = data.pop("user", {})
        data.pop("password", None)
        data.pop("existing_username", None)
        if any(_same_form(k, v) != getattr(role.user, k) for k, v in u.items()):
            check_login_is_this_gyms(role, "username, name, email or mobile number")
        if "username" in u:
            try:
                u["username"] = usernames.validate(u["username"], exclude=role.user)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"username": e.messages})
        for k, v in u.items():
            setattr(role.user, k, v or None if k in ("phone", "email") else v)
        try:
            with transaction.atomic():
                role.user.save()
        except IntegrityError:
            raise serializers.ValidationError({"username": ["That username was just taken. Pick another."]})
        branches = data.pop("branches", None)
        for k, v in data.items():
            setattr(role, k, v)
        role.save()
        if branches is not None:
            role.branches.set(branches)
        return role


class StaffPasswordSerializer(serializers.Serializer):
    """A new password an admin sets for a receptionist or trainer, and tells them."""

    password = serializers.CharField(write_only=True, max_length=128)

    def validate_password(self, value):
        try:
            validate_password(value, self.context.get("user"))
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class SupportAccessSerializer(serializers.ModelSerializer):
    """A window an admin opened for Dumbelo support. `open` says whether it is running right now."""

    hours = serializers.IntegerField(write_only=True, min_value=1, max_value=72, help_text="How long Dumbelo support may look")
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
            raise RuleBroken("already_open", "Dumbelo already has access. End it first to change how long it lasts.")
        return SupportAccess.objects.create(gym=req.gym, granted_by=req.user, starts=now, ends=now + timedelta(hours=data["hours"]))
