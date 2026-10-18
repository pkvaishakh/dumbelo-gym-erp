import re

from django.urls import reverse
from rest_framework import serializers

from apps.billing.models import GymBilling
from apps.gyms.models import Gym

from .models import PLACEHOLDER, Message, WhatsAppAccount, WhatsAppTemplate

META_ID = re.compile(r"^\d{5,32}$")  # Meta's ids are long numbers; nothing else may reach a Graph API path
DISPLAY_NUMBER = re.compile(r"^\+?[\d ()-]{6,23}$")
TEMPLATE_NAME = re.compile(r"^[a-z0-9_]{1,512}$")
LANGUAGE = re.compile(r"^[a-z]{2,3}(_[A-Z]{2})?$")


class MessageSerializer(serializers.ModelSerializer):
    """A message as the desk sees it: when it went, what it said, and whether it arrived."""

    member_name = serializers.CharField(source="member.name", read_only=True, allow_null=True, default=None)
    kind_label = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "member", "member_name", "kind", "kind_label", "to", "text", "for_date", "status", "error", "created_at"]
        read_only_fields = fields

    def get_kind_label(self, message) -> str:
        return message.get_kind_display()


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
