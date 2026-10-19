import re
from typing import Literal

from django.urls import reverse
from rest_framework import serializers

from apps.billing.models import GymBilling
from apps.gyms.models import Gym

from .models import PLACEHOLDER, AutomationSchedule, Message, NotificationRule, WhatsAppAccount, WhatsAppTemplate
from .services import can_retry

META_ID = re.compile(r"^\d{5,32}$")  # Meta's ids are long numbers; nothing else may reach a Graph API path
DISPLAY_NUMBER = re.compile(r"^\+?[\d ()-]{6,23}$")
TEMPLATE_NAME = re.compile(r"^[a-z0-9_]{1,512}$")
LANGUAGE = re.compile(r"^[a-z]{2,3}(_[A-Z]{2})?$")


class MessageSerializer(serializers.ModelSerializer):
    """A message as the gym sees it: who it went to, when, what it said, whether it arrived, and whether an admin may
    send it again (`can_retry`)."""

    member_name = serializers.CharField(source="member.name", read_only=True, allow_null=True, default=None)
    to_name = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    kind_label = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_retry = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "member", "member_name", "user", "to_name", "recipient", "kind", "kind_label", "to", "text", "for_date",
                  "status", "status_label", "error", "attempts", "can_retry", "created_at", "updated_at", "delivered_at", "read_at"]
        read_only_fields = fields

    def get_kind_label(self, message) -> str:
        return message.get_kind_display()

    def get_to_name(self, message) -> str:
        return (message.member or message.user).name

    def get_recipient(self, message) -> Literal["member", "staff"]:
        return "member" if message.member_id else "staff"

    def get_can_retry(self, message) -> bool:
        return can_retry(message)


class ConsoleMessageSerializer(serializers.ModelSerializer):
    """A message in the Console's WhatsApp log: which gym, number and template, and how it went. Never who it went
    to or what it said (a member's name, what they owe): only the last 4 digits of the number."""

    gym_name = serializers.CharField(source="gym.name", read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    recipient = serializers.SerializerMethodField()
    to_last4 = serializers.SerializerMethodField()
    account_number = serializers.CharField(source="account.display_number", read_only=True, allow_null=True, default=None)
    is_shared = serializers.SerializerMethodField()
    template_name = serializers.CharField(source="template.name", read_only=True, allow_null=True, default=None)
    template_language = serializers.CharField(source="template.language", read_only=True, allow_null=True, default=None)

    class Meta:
        model = Message
        fields = ["id", "gym", "gym_name", "kind", "kind_label", "recipient", "to_last4", "account", "account_number", "is_shared",
                  "template", "template_name", "template_language", "for_date", "status", "status_label", "attempts",
                  "next_retry_at", "error_code", "error", "provider_id", "billable", "rate_paise", "created_at", "updated_at",
                  "delivered_at", "read_at"]
        read_only_fields = fields

    def get_recipient(self, message) -> Literal["member", "staff"]:
        return "member" if message.member_id else "staff"

    def get_to_last4(self, message) -> str:
        return message.to[-4:]

    def get_is_shared(self, message) -> bool:
        """Sent from Rackline's shared number (an account with no gym)."""
        return message.account is not None and message.account.gym_id is None


# ---- When messages go out, and their switches ----

class RuleSerializer(serializers.Serializer):
    """One message for one gym: on or paused, who switches it, and when it goes (Rackline's times or the gym's own)."""

    kind = serializers.ChoiceField(choices=WhatsAppTemplate.KINDS)
    label = serializers.CharField()
    is_on = serializers.BooleanField()
    switched_by = serializers.SerializerMethodField(help_text="Who pauses and resumes it: the gym's admins or Rackline")
    hour = serializers.IntegerField(allow_null=True, help_text="The hour it goes out (0-23, the gym's clock); empty when it goes as it happens")
    days_ahead = serializers.ListField(child=serializers.IntegerField(), allow_null=True,
                                       help_text="A plan ending soon: how many days before the end")
    gyms_own_time = serializers.BooleanField(help_text="A Rackline admin set this gym's time in place of Rackline's")

    def get_switched_by(self, rule) -> Literal["gym", "rackline"]:
        return "rackline" if rule.kind in NotificationRule.RACKLINE_KINDS else "gym"


class SwitchSerializer(serializers.Serializer):
    """Pause or Resume. The only thing a gym's admins change about a message: when it goes is Rackline's."""

    is_on = serializers.BooleanField()

    def to_internal_value(self, data):
        # Refused, not ignored, and before anything else: an admin trying to set a time should hear why it can't be
        if extra := set(data if isinstance(data, dict) else ()) - {"is_on"}:
            raise serializers.ValidationError({f: "Rackline sets when messages go out. Contact Rackline to change it." for f in extra})
        return super().to_internal_value(data)


def _hour(**kw):
    return serializers.IntegerField(min_value=0, max_value=23, error_messages={
        "min_value": "Pick an hour from 0 (midnight) to 23 (11 PM)", "max_value": "Pick an hour from 0 (midnight) to 23 (11 PM)"}, **kw)


def _days(**kw):
    return serializers.ListField(child=serializers.IntegerField(min_value=1, max_value=60), min_length=1, max_length=3,
                                 error_messages={"min_length": "Pick at least one day", "max_length": "Pick up to 3 days"}, **kw)


class GymTimesSerializer(serializers.Serializer):
    """A Rackline admin's word on one of a gym's messages: its own hour and days (null for both: Use Rackline's
    Times), and Pause or Resume for the messages Rackline sends the owner."""

    hour = _hour(required=False, allow_null=True)
    days_ahead = _days(required=False, allow_null=True)
    is_on = serializers.BooleanField(required=False)


class AutomationScheduleSerializer(serializers.ModelSerializer):
    """Rackline's times, for every gym that has no times of its own."""

    reminder_hour = _hour()
    days_ahead = _days()
    invoice_hour = _hour()
    updated_by_name = serializers.CharField(source="updated_by.name", read_only=True, allow_null=True, default=None)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = AutomationSchedule
        fields = ["reminder_hour", "days_ahead", "invoice_hour", "updated_at", "updated_by_name"]


# ---- WhatsApp accounts (the Console) ----
# Credentials go in through their own fields and never come out: an account is shown with the last 4 characters
# of each. The querysets behind these leave the encrypted columns unread (WhatsAppAccount.SECRET_FIELDS).

def webhook_path(account: WhatsAppAccount) -> str:
    """Where Meta posts this number's delivery updates: one path for the shared number, one per gym's own."""
    return reverse("whatsapp-webhook") if account.is_shared else reverse("whatsapp-webhook-own", args=[account.webhook_slug])


class WhatsAppAccountSerializer(serializers.ModelSerializer):
    """An account as Rackline admins see it. `template_count` comes from the queryset."""

    gym_name = serializers.CharField(source="gym.name", read_only=True, allow_null=True, default=None)
    is_shared = serializers.BooleanField(read_only=True)
    status = serializers.ChoiceField(choices=WhatsAppAccount.STATUS, read_only=True)
    webhook_url = serializers.SerializerMethodField(help_text="Typed into Meta's webhook settings, with the verify token")
    template_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = WhatsAppAccount
        fields = [
            "id", "gym", "gym_name", "is_shared", "waba_id", "phone_number_id", "display_number", "verified_name",
            "access_token_last4", "app_secret_last4", "webhook_url", "verify_token", "status", "checked_at", "last_error",
            "template_count", "created_at",
        ]
        read_only_fields = fields

    def get_webhook_url(self, account) -> str:
        request = self.context.get("request")
        path = webhook_path(account)
        return request.build_absolute_uri(path) if request else path


class _Where(serializers.Serializer):
    waba_id = serializers.RegexField(META_ID, help_text="Meta's WhatsApp Business account id",
                                     error_messages={"invalid": "Use the WhatsApp Business account id from Meta: digits only"})
    phone_number_id = serializers.RegexField(META_ID, help_text="Meta's phone number id (not the number itself)",
                                             error_messages={"invalid": "Use the phone number id from Meta: digits only"})
    display_number = serializers.RegexField(DISPLAY_NUMBER, error_messages={"invalid": "Type the number as people see it, e.g. +91 98000 00000"})


def _secret(**kw):
    """A credential: in only, trimmed, and never echoed back in an error."""
    return serializers.CharField(write_only=True, trim_whitespace=True, style={"input_type": "password"},
                                 error_messages={"max_length": "That's too long for a credential: check what was pasted"}, **kw)


class WhatsAppAccountCreateSerializer(_Where):
    """Add Account. No gym means Rackline's shared number."""

    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all(), allow_null=True, required=False, default=None,
                                             help_text="The gym whose own number this is; leave out for Rackline's shared number")
    access_token = _secret(min_length=20, max_length=1024, help_text="A permanent access token for the number (a system user's)")
    app_secret = _secret(min_length=16, max_length=256, help_text="The Meta app's secret, which signs its webhook calls")


class WhatsAppAccountChangeSerializer(_Where):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class CredentialsSerializer(serializers.Serializer):
    """Replace Credentials: either or both. The ones left out stay as they are."""

    access_token = _secret(min_length=20, max_length=1024, required=False)
    app_secret = _secret(min_length=16, max_length=256, required=False)

    def validate(self, data):
        if not data.get("access_token") and not data.get("app_secret"):
            raise serializers.ValidationError({"access_token": ["Paste a new access token, a new app secret, or both"]})
        return data


class WhatsAppTemplateSerializer(serializers.ModelSerializer):
    kind = serializers.ChoiceField(choices=WhatsAppTemplate.KINDS, read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    category = serializers.ChoiceField(choices=WhatsAppTemplate.CATEGORIES, read_only=True)
    status = serializers.ChoiceField(choices=WhatsAppTemplate.STATUS, read_only=True)
    parameters = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = WhatsAppTemplate
        fields = ["id", "account", "kind", "kind_label", "name", "language", "category", "body", "parameters", "status", "updated_at"]
        read_only_fields = fields


class WhatsAppTemplateInputSerializer(serializers.Serializer):
    """Add Template and Edit Template. On an edit, what's left out stays as it was."""

    account = serializers.PrimaryKeyRelatedField(queryset=WhatsAppAccount.objects.only("pk"), help_text="Only when adding")
    kind = serializers.ChoiceField(choices=WhatsAppTemplate.KINDS)
    name = serializers.RegexField(TEMPLATE_NAME, max_length=512,
                                  error_messages={"invalid": "Use the name exactly as it is in Meta: lower-case letters, numbers and _"})
    language = serializers.RegexField(LANGUAGE, default="en", error_messages={"invalid": "Use Meta's language code, e.g. en or en_US"})
    category = serializers.ChoiceField(choices=WhatsAppTemplate.CATEGORIES, default=WhatsAppTemplate.UTILITY)
    body = serializers.CharField(max_length=1024, help_text="The text as Meta approved it, with {{1}}, {{2}}…")
    parameters = serializers.ListField(child=serializers.CharField(max_length=40), max_length=10, allow_empty=True,
                                       help_text="Which detail fills {{1}}, {{2}}…, in order")
    status = serializers.ChoiceField(choices=WhatsAppTemplate.STATUS, default=WhatsAppTemplate.PENDING)

    def validate(self, data):
        template = self.instance
        kind = data.get("kind", template and template.kind)
        params = data.get("parameters", template.parameters if template else [])
        body = data.get("body", template and template.body)
        allowed = WhatsAppTemplate.PARAMETERS[kind]
        if unknown := [p for p in params if p not in allowed]:
            raise serializers.ValidationError({"parameters": [f"{', '.join(unknown)} can't go in this message. It can use {', '.join(allowed)}"]})
        if len(set(params)) != len(params):
            raise serializers.ValidationError({"parameters": ["Name each detail once"]})
        found = {int(n) for n in PLACEHOLDER.findall(body)}
        if template and "account" in data and data["account"].pk != template.account_id:
            raise serializers.ValidationError({"account": ["A template stays with its number. Add it to the other number instead"]})
        if found != set(range(1, len(params) + 1)):
            want = ", ".join(f"{{{{{i}}}}}" for i in range(1, len(params) + 1)) or "no {{n}} at all"
            raise serializers.ValidationError({"body": [f"With {len(params)} details, the text needs {want}, as Meta approved it"]})
        return data


class TemplateParameterSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()


class MessageKindSerializer(serializers.Serializer):
    """A message Rackline sends, and the details a template for it can use."""

    kind = serializers.ChoiceField(choices=WhatsAppTemplate.KINDS)
    label = serializers.CharField()
    parameters = TemplateParameterSerializer(many=True)


def message_kinds() -> list[dict]:
    return [
        {"kind": kind, "label": label, "parameters": [{"name": n, "label": t} for n, t in WhatsAppTemplate.PARAMETERS[kind].items()]}
        for kind, label in WhatsAppTemplate.KINDS
    ]


# ---- A gym's own view: More → Settings → WhatsApp ----

class GymWhatsAppSerializer(serializers.Serializer):
    """How the gym's messages go out, the number they come from and whether it works. Never any credential."""

    NOT_SET_UP, OFF = "not_set_up", "off"
    STATES = [*WhatsAppAccount.STATUS, (NOT_SET_UP, "Not set up yet"), (OFF, "Off")]

    mode = serializers.ChoiceField(choices=GymBilling.WHATSAPP_MODES)
    number = serializers.CharField(allow_null=True, help_text="The number members see messages from")
    verified_name = serializers.CharField(allow_blank=True)
    status = serializers.ChoiceField(choices=STATES)
    checked_at = serializers.DateTimeField(allow_null=True)

    @staticmethod
    def of(mode: str, account: WhatsAppAccount | None) -> dict:
        if mode == GymBilling.OFF:
            status = GymWhatsAppSerializer.OFF
        else:
            status = account.status if account else GymWhatsAppSerializer.NOT_SET_UP
        return {
            "mode": mode, "number": account.display_number if account else None, "verified_name": account.verified_name if account else "",
            "status": status, "checked_at": account.checked_at if account else None,
        }


# ---- Usage on Rackline's shared number ----

class UsageLineSerializer(serializers.Serializer):
    category = serializers.CharField(help_text="Meta's category for the template: utility, marketing or authentication")
    rate_paise = serializers.IntegerField(help_text="What each one costs once delivered")
    messages = serializers.IntegerField()
    amount_paise = serializers.IntegerField()


class GymUsageSerializer(serializers.Serializer):
    """The gym's messages delivered from Rackline's shared number in its billing month so far, and what they come
    to on the invoice written on `billed_on`."""

    mode = serializers.ChoiceField(choices=GymBilling.WHATSAPP_MODES)
    starts = serializers.DateField()
    ends = serializers.DateField()
    billed_on = serializers.DateField(help_text="The invoice these go on is written this day")
    messages = serializers.IntegerField()
    amount_paise = serializers.IntegerField()
    lines = UsageLineSerializer(many=True)


class GymUsageRowSerializer(serializers.Serializer):
    gym = serializers.IntegerField()
    gym_name = serializers.CharField()
    messages = serializers.IntegerField()
    amount_paise = serializers.IntegerField()


class ConsoleUsageSerializer(serializers.Serializer):
    """A page of gyms by what their shared-number messages came to in a month, with the month's totals."""

    month = serializers.CharField(help_text="YYYY-MM")
    messages = serializers.IntegerField(help_text="Every gym's, this month")
    amount_paise = serializers.IntegerField()
    count = serializers.IntegerField(help_text="Gyms with any")
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = GymUsageRowSerializer(many=True)
