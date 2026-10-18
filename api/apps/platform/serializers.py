import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.errors import RuleBroken
from apps.gyms.models import Branch, Gym, GymRole

from .services import check_timezone, find_login

SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")


def _timezone(value):
    try:
        return check_timezone(value)
    except RuleBroken as e:  # shown under the field rather than as a 409
        raise serializers.ValidationError(str(e.detail))


def _password(value, user=None):
    try:
        validate_password(value, user)
    except DjangoValidationError as e:
        raise serializers.ValidationError(list(e.messages))
    return value


class GymRowSerializer(serializers.ModelSerializer):
    """A gym in the Console's list. The counts and the owner come from the queryset (`views.gyms`)."""

    status = serializers.ChoiceField(choices=Gym.STATUS, read_only=True)
    branch_count = serializers.IntegerField(read_only=True, help_text="Active branches")
    member_count = serializers.IntegerField(read_only=True, help_text="Members, leaving out archived ones")
    owner_name = serializers.CharField(read_only=True, allow_null=True)
    owner_email = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Gym
        fields = ["id", "name", "slug", "status", "timezone", "billing_email", "branch_count", "member_count", "owner_name", "owner_email", "created_at"]
        read_only_fields = fields  # output only: New Gym and edits have their own serializers


class GymBranchSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Branch
        fields = ["id", "name", "is_active", "member_count"]


class GymDetailSerializer(GymRowSerializer):
    """One gym: its status and why it last changed, and its branches. Its admins are their own list."""

    branches = GymBranchSerializer(many=True, read_only=True, source="branch_rows")

    class Meta(GymRowSerializer.Meta):
        fields = GymRowSerializer.Meta.fields + ["status_reason", "status_changed_at", "branches"]
        read_only_fields = fields


class NewGymSerializer(GymDetailSerializer):
    owner_new_login = serializers.BooleanField(read_only=True, help_text="False: the owner already had a Rackline login and keeps their password")

    class Meta(GymDetailSerializer.Meta):
        fields = GymDetailSerializer.Meta.fields + ["owner_new_login"]
        read_only_fields = fields


class GymCreateSerializer(serializers.Serializer):
    """New Gym: the gym, its first branch and its owner admin (a new login, or the one they already have)."""

    name = serializers.CharField(max_length=120)
    slug = serializers.CharField(max_length=40, help_text="Short name the app sends as X-Gym: lowercase letters, numbers and dashes")
    timezone = serializers.CharField(max_length=40, default="Asia/Kolkata")
    branch = serializers.CharField(max_length=80, help_text="The first branch's name")
    owner_name = serializers.CharField(max_length=120, required=False, allow_blank=True, help_text="Needed for a new login")
    owner_email = serializers.EmailField(max_length=254)
    owner_password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True, help_text="Needed for a new login")
    billing_email = serializers.EmailField(max_length=254, required=False, allow_blank=True, help_text="The owner's email if left out")

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Enter the gym's name")
        return value.strip()

    def validate_branch(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name the first branch")
        return value.strip()

    def validate_slug(self, value):
        value = value.strip().lower()
        if not SLUG.match(value):
            raise serializers.ValidationError("Use 3 to 40 lowercase letters, numbers and dashes, like iron-house")
        if Gym.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Another gym already uses this short name")
        return value

    def validate_timezone(self, value):
        return _timezone(value)

    def validate_owner_password(self, value):
        return _password(value) if value else value

    def validate(self, data):
        if find_login(data["owner_email"]) is None:  # a new login needs a name and a first password
            errors = {}
            if not data.get("owner_name", "").strip():
                errors["owner_name"] = "Enter the owner's name"
            if not data.get("owner_password"):
                errors["owner_password"] = "They don't sign in to Rackline yet: set a first password and tell them"
            if errors:
                raise serializers.ValidationError(errors)
        return data


class GymEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ["name", "timezone", "billing_email"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Enter the gym's name")
        return value.strip()

    def validate_timezone(self, value):
        return _timezone(value)


class StatusChangeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200, help_text="Why, for the gym's history")

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("Say why, for the gym's history")
        return value.strip()


class GymAdminSerializer(serializers.ModelSerializer):
    """An admin of the gym. `other_gyms` counts the other gyms the same login opens: a new password works there too."""

    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True, allow_null=True)
    phone = serializers.CharField(source="user.phone", read_only=True, allow_null=True)
    other_gyms = serializers.IntegerField(read_only=True)

    class Meta:
        model = GymRole
        fields = ["id", "name", "email", "phone", "is_owner", "is_active", "other_gyms"]
        read_only_fields = fields


class GymAdminAddSerializer(serializers.Serializer):
    """Add Admin: their email, and for someone new to Rackline, their name and a first password."""

    email = serializers.EmailField(max_length=254)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True)

    def validate_password(self, value):
        return _password(value) if value else value

    def validate(self, data):
        if find_login(data["email"]) is None:
            errors = {}
            if not data.get("name", "").strip():
                errors["name"] = "Enter their name"
            if not data.get("password"):
                errors["password"] = "They don't sign in to Rackline yet: set a first password and tell them"
            if errors:
                raise serializers.ValidationError(errors)
        return data
