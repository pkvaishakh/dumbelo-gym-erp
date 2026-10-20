from rest_framework import serializers

from apps.accounts.models import normalize_phone

from .models import Lead

TRIMMED = ("name", "gym_name", "city", "note", "utm_source", "utm_medium", "utm_campaign")


class LeadAskSerializer(serializers.ModelSerializer):
    """What the landing page's form sends. `website` is a field people never see: a bot that fills it in is
    thanked and dropped."""

    name = serializers.CharField(max_length=100, error_messages={"blank": "Enter your name", "required": "Enter your name"})
    phone = serializers.CharField(max_length=20, error_messages={"blank": "Enter your mobile number", "required": "Enter your mobile number"})
    gym_name = serializers.CharField(max_length=120, error_messages={"blank": "Enter your gym’s name", "required": "Enter your gym’s name"})
    city = serializers.CharField(max_length=80, error_messages={"blank": "Enter your city", "required": "Enter your city"})
    branches = serializers.ChoiceField(choices=Lead.BRANCHES, error_messages={"invalid_choice": "Choose how many branches", "required": "Choose how many branches"})
    email = serializers.EmailField(required=False, allow_blank=True, error_messages={"invalid": "Enter an email like you@gym.com, or leave it empty"})
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
    utm_source = serializers.CharField(max_length=100, required=False, allow_blank=True)
    utm_medium = serializers.CharField(max_length=100, required=False, allow_blank=True)
    utm_campaign = serializers.CharField(max_length=100, required=False, allow_blank=True)
    website = serializers.CharField(max_length=200, required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Lead
        fields = ["name", "phone", "email", "gym_name", "city", "branches", "note", "utm_source", "utm_medium", "utm_campaign", "website"]

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except Exception:
            raise serializers.ValidationError("Enter a 10-digit mobile number")

    def validate(self, attrs):
        for field in TRIMMED:
            if field in attrs:
                attrs[field] = " ".join(attrs[field].split())
        return attrs


class LeadReceivedSerializer(serializers.Serializer):
    received = serializers.BooleanField()


class ConsoleLeadSerializer(serializers.ModelSerializer):
    branches_label = serializers.CharField(source="get_branches_display")
    status_by_name = serializers.CharField(source="status_by.name", default=None, allow_null=True)

    class Meta:
        model = Lead
        fields = ["id", "name", "phone", "email", "gym_name", "city", "branches", "branches_label", "note", "utm_source",
                  "utm_medium", "utm_campaign", "status", "status_by_name", "status_at", "created_at"]


class LeadStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Lead.STATUSES)
