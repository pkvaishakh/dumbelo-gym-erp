import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts import usernames
from apps.core.errors import RuleBroken
from apps.core.models import JobRun
from apps.gyms.models import Branch, Gym, GymRole

from . import server
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


def _new_username(value):
    if not value:
        return value
    try:
        return usernames.validate(value)
    except DjangoValidationError as e:
        raise serializers.ValidationError(e.messages[0])


def _check_login(data, *, existing, name, password, name_message):
    """Someone who already signs in is added by their username; a new login needs a name and a first password."""
    if data.get(existing):
        user = find_login(data[existing])
        if user is None:
            raise serializers.ValidationError({existing: "No one signs in with that username"})
        if user.is_staff:
            raise serializers.ValidationError({existing: "That's a Dumbelo team login. Use the gym admin's own username."})
        return
    errors = {}
    if not data.get(name, "").strip():
        errors[name] = name_message
    if not data.get(password):
        errors[password] = "They don't sign in to Dumbelo yet: set a first password and tell them"
    if errors:
        raise serializers.ValidationError(errors)


class GymRowSerializer(serializers.ModelSerializer):
    """A gym in the Console's list. The counts and the owner come from the queryset (`views.gyms`)."""

    status = serializers.ChoiceField(choices=Gym.STATUS, read_only=True)
    branch_count = serializers.IntegerField(read_only=True, help_text="Active branches")
    member_count = serializers.IntegerField(read_only=True, help_text="Members, leaving out archived ones")
    owner_name = serializers.CharField(read_only=True, allow_null=True)
    owner_email = serializers.CharField(read_only=True, allow_null=True)
    owner_username = serializers.CharField(read_only=True, allow_null=True, help_text="How the owner signs in")
    owed_paise = serializers.IntegerField(read_only=True, help_text="What its open Dumbelo invoices still owe")

    class Meta:
        model = Gym
        fields = ["id", "name", "slug", "status", "timezone", "billing_email", "branch_count", "member_count", "owner_name", "owner_email", "owner_username", "owed_paise", "created_at"]
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
    owner_new_login = serializers.BooleanField(read_only=True, help_text="False: the owner already had a Dumbelo login and keeps their password")

    class Meta(GymDetailSerializer.Meta):
        fields = GymDetailSerializer.Meta.fields + ["owner_new_login"]
        read_only_fields = fields


class GymCreateSerializer(serializers.Serializer):
    """New Gym: the gym, its first branch and its owner admin (a new login, or the one they already have)."""

    name = serializers.CharField(max_length=120)
    slug = serializers.CharField(max_length=40, help_text="Short name the app sends as X-Gym: lowercase letters, numbers and dashes")
    timezone = serializers.CharField(max_length=40, default="Asia/Kolkata")
    branch = serializers.CharField(max_length=80, help_text="The first branch's name")
    owner_existing_username = serializers.CharField(max_length=60, required=False, allow_blank=True,
                                                    help_text="The owner already signs in to Dumbelo (another gym): their username")
    owner_username = serializers.CharField(max_length=60, required=False, allow_blank=True,
                                           help_text="A new login's username; made from the email or name if left out")
    owner_name = serializers.CharField(max_length=120, required=False, allow_blank=True, help_text="Needed for a new login")
    owner_email = serializers.EmailField(max_length=254, required=False, allow_blank=True, help_text="For contact, and invoices unless billing_email is given")
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

    def validate_owner_username(self, value):
        return _new_username(value)

    def validate(self, data):
        _check_login(data, existing="owner_existing_username", name="owner_name", password="owner_password",
                     name_message="Enter the owner's name")
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

    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True, allow_null=True)
    phone = serializers.CharField(source="user.phone", read_only=True, allow_null=True)
    other_gyms = serializers.IntegerField(read_only=True)

    class Meta:
        model = GymRole
        fields = ["id", "username", "name", "email", "phone", "is_owner", "is_active", "other_gyms"]
        read_only_fields = fields


class GymAdminAddSerializer(serializers.Serializer):
    """Add Admin: the username of someone who already signs in to Dumbelo, or for someone new, their name, a first
    password, and a username (made from their email or name if left out)."""

    existing_username = serializers.CharField(max_length=60, required=False, allow_blank=True)
    username = serializers.CharField(max_length=60, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=254, required=False, allow_blank=True)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True)

    def validate_password(self, value):
        return _password(value) if value else value

    def validate_username(self, value):
        return _new_username(value)

    def validate(self, data):
        _check_login(data, existing="existing_username", name="name", password="password", name_message="Enter their name")
        return data


# ---- The Server screen (server.py) ----

class JobCountSerializer(serializers.Serializer):
    label = serializers.CharField()
    count = serializers.IntegerField()


class JobRunSerializer(serializers.ModelSerializer):
    """One run of a job: who started it, how long it took and what it did, in words."""

    QUEUED, RUNNING, DONE, FAILED = "queued", "running", "done", "failed"
    STATES = [(QUEUED, "Waiting for the worker"), (RUNNING, "Running"), (DONE, "Done"), (FAILED, "Failed")]

    trigger_label = serializers.CharField(source="get_trigger_display", read_only=True)
    by_name = serializers.CharField(source="by.name", read_only=True, allow_null=True, default=None)
    state = serializers.SerializerMethodField()
    seconds = serializers.SerializerMethodField()
    did = serializers.SerializerMethodField()

    class Meta:
        model = JobRun
        fields = ["id", "job", "trigger", "trigger_label", "by_name", "created_at", "started_at", "finished_at", "state",
                  "seconds", "did", "error"]
        read_only_fields = fields

    @extend_schema_field(serializers.ChoiceField(choices=STATES))
    def get_state(self, run) -> str:
        if run.finished_at is None:
            return self.QUEUED if run.started_at is None else self.RUNNING
        return self.FAILED if run.error else self.DONE

    def get_seconds(self, run) -> float | None:
        """How long it took, once it has finished."""
        if run.started_at is None or run.finished_at is None:
            return None
        return round((run.finished_at - run.started_at).total_seconds(), 1)

    @extend_schema_field(JobCountSerializer(many=True))
    def get_did(self, run):
        """Its counts that aren't zero, in the job's order and words; empty when it found nothing to do."""
        labels = server.JOBS[run.job].counts if run.job in server.JOBS else []
        return [{"label": label, "count": run.counts[key]} for key, label in labels if run.counts.get(key)]


class CheckSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=server.CHECKS)
    label = serializers.CharField()
    state = serializers.ChoiceField(choices=server.STATES)
    detail = serializers.CharField()
    at = serializers.DateTimeField(allow_null=True, help_text="Beat's last tick")


class JobStatusSerializer(serializers.Serializer):
    job = serializers.ChoiceField(choices=JobRun.JOBS)
    label = serializers.CharField()
    schedule = serializers.CharField()
    can_run = serializers.BooleanField(help_text="Run Now can start it")
    current = JobRunSerializer(allow_null=True, help_text="Its run waiting or under way")
    last_run = JobRunSerializer(allow_null=True, help_text="Its last finished run")


class MessageCountsSerializer(serializers.Serializer):
    waiting_retry = serializers.IntegerField()
    failed_today = serializers.IntegerField()


class NumberCallSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_number = serializers.CharField()
    gym_name = serializers.CharField(allow_null=True)
    is_shared = serializers.BooleanField()
    last_call_at = serializers.DateTimeField(allow_null=True, help_text="Meta's last call to this number's webhook")


class WebhookStatusSerializer(serializers.Serializer):
    failed_days = serializers.IntegerField()
    failed = serializers.IntegerField(help_text="Calls in the last `failed_days` days that couldn't be handled")
    numbers = NumberCallSerializer(many=True)


class ServerStatusSerializer(serializers.Serializer):
    version = serializers.CharField()
    deployed_at = serializers.DateTimeField(allow_null=True)
    checked_at = serializers.DateTimeField()
    checks = CheckSerializer(many=True)
    jobs = JobStatusSerializer(many=True, allow_null=True, help_text="Null while the database can't be read")
    messages = MessageCountsSerializer(allow_null=True)
    webhook = WebhookStatusSerializer(allow_null=True)


class GymCountsSerializer(serializers.Serializer):
    active = serializers.IntegerField()
    trial = serializers.IntegerField()
    suspended = serializers.IntegerField()
    new_this_month = serializers.IntegerField(help_text="Gyms added since the 1st, whatever their status now")


class OwedSerializer(serializers.Serializer):
    owed_paise = serializers.IntegerField(help_text="What every gym owes Dumbelo on its open invoices")
    gyms_owing = serializers.IntegerField()
    overdue_paise = serializers.IntegerField(help_text="The part of it on invoices past their due day")
    overdue_invoices = serializers.IntegerField()
    gyms_overdue = serializers.IntegerField()


class WaitingSerializer(serializers.Serializer):
    waiting = serializers.IntegerField()


class WhatsAppDaySerializer(serializers.Serializer):
    delivered_today = serializers.IntegerField(help_text="On every number")
    failed_today = serializers.IntegerField()
    waiting_retry = serializers.IntegerField()
    shared_messages = serializers.IntegerField(help_text="Billable messages on the shared number delivered this month")
    shared_paise = serializers.IntegerField(help_text="What those come to, at the rate kept on each")


class FailedJobSerializer(serializers.Serializer):
    job = serializers.ChoiceField(choices=JobRun.JOBS)
    label = serializers.CharField()
    finished_at = serializers.DateTimeField(source="last_run.finished_at")
    error = serializers.CharField(source="last_run.error")


class ServerAttentionSerializer(serializers.Serializer):
    down = CheckSerializer(many=True, help_text="Checks that are down, in the Server screen's order")
    failed_jobs = FailedJobSerializer(many=True, help_text="Jobs whose last run failed")


class NewLeadsSerializer(serializers.Serializer):
    new = serializers.IntegerField(help_text="Demo requests from the landing page no one has answered yet")


class PlatformSummarySerializer(serializers.Serializer):
    """Console → Home. Counts and Dumbelo's own money only: nothing from inside a gym."""

    checked_at = serializers.DateTimeField()
    gyms = GymCountsSerializer()
    money = OwedSerializer()
    branch_requests = WaitingSerializer()
    leads = NewLeadsSerializer()
    whatsapp = WhatsAppDaySerializer()
    server = ServerAttentionSerializer()
