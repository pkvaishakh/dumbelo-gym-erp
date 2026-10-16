from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """A reminder as the desk sees it: when it went, what it said, and whether it arrived."""

    member_name = serializers.CharField(source="member.name", read_only=True)
    kind_label = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "member", "member_name", "kind", "kind_label", "to", "text", "for_date", "status", "error", "created_at"]

    def get_kind_label(self, message) -> str:
        return message.get_kind_display()
