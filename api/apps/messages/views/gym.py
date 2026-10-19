"""The gym's own side of messages: the ones it has sent (and Retry), its shared-number usage, how its WhatsApp is set
up, and its message switches."""
import re
from datetime import timedelta

import django_filters
from django.db.models import Q
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.billing.models import GymBilling
from apps.billing.services import billing_month
from apps.core import clock
from apps.core.params import open_days
from apps.core.tenancy import ADMIN, DESK, GymViewMixin

from .. import automation, services
from .. import usage as shared_usage
from ..accounts import account_for, whatsapp_mode
from ..models import Message, NotificationRule
from ..serializers import GymUsageSerializer, GymWhatsAppSerializer, MessageSerializer, RuleSerializer, SwitchSerializer


class MessageFilter(django_filters.FilterSet):
    """`?member=`, `?kind=`, `?status=`, and `?recipient=member|staff`."""

    recipient = django_filters.ChoiceFilter(choices=[("member", "A member"), ("staff", "A staff member")], method="filter_recipient")

    class Meta:
        model = Message
        fields = ["member", "kind", "status"]

    def filter_recipient(self, qs, name, value):
        return qs.filter(member__isnull=value == "staff")


_LOG_FILTERS = [
    OpenApiParameter("q", str, description="Their name or number (4 digits or more), 2 characters or more"),
    OpenApiParameter("from", str, description="For this day or later (the gym's days), YYYY-MM-DD"),
    OpenApiParameter("to", str, description="For this day or earlier, YYYY-MM-DD"),
]


@extend_schema_view(list=extend_schema(parameters=_LOG_FILTERS))
class MessageViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The messages a gym has sent, newest first: More → Messages, and a member's profile.

    Messages go out by themselves; the one thing to post is Retry, for an admin, on a message that failed. Trainers
    and members are out because a dues reminder says the amount; the desk sees only its branches' members' messages.
    """

    serializer_class = MessageSerializer
    roles = {"retry": ADMIN, "usage": ADMIN, "*": DESK}
    filterset_class = MessageFilter

    def get_queryset(self):
        qs = Message.objects.filter(gym=self.gym).select_related("member", "user")
        qs = self.in_my_branches(qs, "member__home_branch")
        first, last = open_days(self.request)
        if first:
            qs = qs.filter(for_date__gte=first)
        if last:
            qs = qs.filter(for_date__lte=last)
        return _search(qs, self.request.query_params.get("q", ""))

    @extend_schema(request=None, responses=MessageSerializer)
    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """Retry: send a failed message again, on the same row and key, so it still goes once at most. Refused for
        one that may have reached them after all. Audited."""
        row = self.get_object()
        before = {"status": row.status, "error": row.error, "to": row.to}
        row = services.retry(row)
        record(request, "message.retried", row, before, {"status": row.status, "error": row.error, "to": row.to})
        return Response(self.get_serializer(row).data)

    @extend_schema(responses=GymUsageSerializer, filters=False)
    @action(detail=False, methods=["get"], pagination_class=None)
    def usage(self, request):
        """This billing month's messages on Dumbelo's shared number, by Meta's category, and what they will come
        to on the next invoice. Two queries."""
        gym, today = self.gym, clock.today(self.gym)
        plan = GymBilling.objects.filter(gym=gym).first()
        if plan:
            starts, ends = billing_month(plan.billing_day, today)
        else:  # no Dumbelo plan yet: nothing is billed, so the calendar month
            starts, ends = today.replace(day=1), clock.add_months(today.replace(day=1), 1) - timedelta(days=1)
        lines = shared_usage.usage(gym, starts, today)
        return Response(GymUsageSerializer({
            "mode": plan.whatsapp_mode if plan else GymBilling.OFF, "starts": starts, "ends": ends, "billed_on": ends + timedelta(days=1),
            "messages": sum(r["messages"] for r in lines), "amount_paise": sum(r["amount_paise"] for r in lines), "lines": lines,
        }).data)


def _search(qs, text: str):
    """Digits find the number it went to by its end; anything else the member's or staff member's name."""
    text = text.strip()
    if len(text) < 2:
        return qs
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 4 and not re.search(r"[A-Za-z]", text):
        return qs.filter(to__endswith=digits[-10:])
    return qs.filter(Q(member__name__icontains=text) | Q(user__name__icontains=text))


@extend_schema(tags=["gym"])
class GymWhatsAppView(GymViewMixin, APIView):
    """More → Settings → WhatsApp: whether messages go from Dumbelo's number, the gym's own or not at all, the
    number, and whether it works. Admins only; set up by Dumbelo, so there is nothing here to change."""

    roles = {"*": ADMIN}

    @extend_schema(responses=GymWhatsAppSerializer)
    def get(self, request):
        answer = GymWhatsAppSerializer.of(whatsapp_mode(self.gym), account_for(self.gym))
        return Response(GymWhatsAppSerializer(answer).data)


def _kind(kind: str, allowed) -> str:
    if kind not in allowed:
        raise Http404
    return kind


@extend_schema(tags=["gym"])
class GymMessagesView(GymViewMixin, APIView):
    """More → Settings → Messages: each of the gym's messages, on or paused, and when it goes out. Admins only.
    When is Dumbelo's to set, so it is only shown here."""

    roles = {"*": ADMIN}

    @extend_schema(responses=RuleSerializer(many=True))
    def get(self, request):
        rules = automation.rules_for(self.gym)
        return Response(RuleSerializer([rules[k] for k in NotificationRule.GYM_KINDS], many=True).data)


@extend_schema(tags=["gym"], parameters=[OpenApiParameter("kind", str, OpenApiParameter.PATH, enum=list(NotificationRule.GYM_KINDS))])
class GymMessageView(GymViewMixin, APIView):
    """Pause or Resume one of the gym's messages, at every branch. Pausing stops the messages, not the desk's
    reminder list. Audited: it decides what members and staff hear from the gym."""

    roles = {"*": ADMIN}

    @extend_schema(request=SwitchSerializer, responses=RuleSerializer)
    def patch(self, request, kind):
        kind = _kind(kind, NotificationRule.GYM_KINDS)
        s = SwitchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = automation.rules_for(self.gym)[kind]
        row = automation.switch(self.gym, kind, s.validated_data["is_on"], dumbelo=False)
        after = automation.rules_for(self.gym)[kind]
        if before != after:
            record(request, "message.switched", row, automation.audit_rule(before), automation.audit_rule(after))
        return Response(RuleSerializer(after).data)
