"""Personal training: a member's plan with its sessions, and the sessions given."""
from rest_framework import serializers

from .models import Plan, PTSession, Subscription


class PTPlanSerializer(serializers.Serializer):
    """A member's personal training now: its dates, sessions bought and used, and who trains them. No amounts."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    starts = serializers.DateField()
    ends = serializers.DateField()
    sessions = serializers.IntegerField(help_text="Sessions bought")
    sessions_used = serializers.IntegerField()
    trainer = serializers.IntegerField(allow_null=True)
    trainer_name = serializers.CharField(allow_null=True)
    frozen_from = serializers.DateField(allow_null=True)
    frozen_until = serializers.DateField(allow_null=True)


def pt_plan(member, today):
    """The member's personal training now, for PTPlanSerializer, from the plans with_totals() loaded."""
    sub = member.plan_of(Plan.PT, today)
    if sub is None:
        return None
    return {"id": sub.id, "name": sub.plan.name, "starts": sub.starts, "ends": sub.ends, "sessions": sub.sessions,
            "sessions_used": sub.sessions_used(), "trainer": sub.trainer_id, "trainer_name": sub.trainer.user.name if sub.trainer else None,
            "frozen_from": sub.frozen_from, "frozen_until": sub.frozen_until}


class BodyPartsField(serializers.ListField):
    """What they worked, each named once: Chest, Back… as BODY_PARTS spells them, any other as typed."""

    child = serializers.CharField(max_length=30)

    def __init__(self, **kw):
        super().__init__(max_length=12, help_text=f"What they worked: {', '.join(PTSession.BODY_PARTS)}, or any other", **kw)

    def to_internal_value(self, data):
        known = {p.lower(): p for p in PTSession.BODY_PARTS}
        out = {}
        for part in super().to_internal_value(data):
            part = " ".join(part.split())
            out.setdefault(part.lower(), known.get(part.lower(), part))
        return list(out.values())


class PTSessionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.name", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True)
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)
    marked_by_name = serializers.CharField(source="marked_by.user.name", read_only=True)
    body_parts = serializers.ListField(child=serializers.CharField(), read_only=True, help_text="What they worked")

    class Meta:
        model = PTSession
        fields = ["id", "member", "member_name", "subscription", "plan_name", "trainer", "trainer_name", "local_date", "body_parts", "notes",
                  "marked_by_name", "marked_at", "voided", "void_reason"]
        read_only_fields = fields


class MarkSessionSerializer(serializers.Serializer):
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.none(), help_text="The personal training plan")
    local_date = serializers.DateField(required=False, help_text="The day it was given; today when left out. Trainers mark today only")
    body_parts = BodyPartsField(required=False)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def __init__(self, *a, queryset=None, **kw):
        super().__init__(*a, **kw)
        if queryset is not None:
            self.fields["subscription"].queryset = queryset


class SessionNotesSerializer(serializers.Serializer):
    """Change what a session worked and its notes. Its day and plan stay; one marked wrong is removed and marked again."""

    body_parts = BodyPartsField(required=False)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
