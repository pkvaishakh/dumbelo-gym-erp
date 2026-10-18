from django.db.models import F
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core import clock
from apps.core.params import day_range, int_param
from apps.core.tenancy import ADMIN, DESK, GymViewMixin
from apps.gyms.models import Branch, GymRole
from apps.members.serializers import VoidSerializer

from .. import services
from ..models import DrawerClose
from ..serializers import BranchCashSerializer, DrawerCloseSerializer, DrawerCountSerializer


def _count(c: DrawerClose) -> dict:
    return {"counted_paise": c.counted_paise, "expected_paise": c.expected_paise, "note": c.note}


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("date", str, description="YYYY-MM-DD: counts for that local day"),
    OpenApiParameter("from", str, description="First local day, YYYY-MM-DD. Admins only when it spans more than a day"),
    OpenApiParameter("to", str, description="Last local day, YYYY-MM-DD"),
    OpenApiParameter("state", str, enum=["to_settle"], description="to_settle: counts that didn't match and aren't settled yet"),
]))
class DrawerCloseViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The desk's end-of-day cash counts: counted, expected and the difference. The desk counts its branches' cash
    and sees one day at a time (today by default), like the day's payments; only admins settle a difference."""

    serializer_class = DrawerCloseSerializer
    roles = {"settle": ADMIN, "*": DESK}
    filterset_fields = ["branch"]

    def get_queryset(self):
        qs = self.in_my_branches(DrawerClose.objects.filter(gym=self.gym).select_related("branch", "counted_by__user", "settled_by__user"))
        if self.action == "list":
            admin = self.me.role in (GymRole.ADMIN, "support")
            days = day_range(self.request, clock.today(self.gym), many_days=admin, what="counts")
            if days is None and not admin:
                days = (clock.today(self.gym),) * 2
            if days:
                qs = qs.filter(day__gte=days[0], day__lte=days[1])
            if self.request.query_params.get("state") == "to_settle":
                qs = qs.filter(settled_at__isnull=True).exclude(counted_paise=F("expected_paise"))
        return qs

    @extend_schema(request=DrawerCountSerializer, responses={201: DrawerCloseSerializer})
    def create(self, request, *args, **kwargs):
        """Count the drawer: today's count for the branch, against what its cash in hand holds now. Counting again
        the same day replaces it, until an admin settles the difference."""
        body = DrawerCountSerializer(data=request.data, context=self.get_serializer_context())
        body.is_valid(raise_exception=True)
        d = body.validated_data
        close, before = services.close_drawer(d["branch"], counted_paise=d["counted_paise"], by=self.me, note=d.get("note", ""))
        record(request, "drawer.recounted" if before else "drawer.counted", close, before, _count(close))
        return Response(self.get_serializer(self.get_queryset().get(pk=close.pk)).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=VoidSerializer, responses=DrawerCloseSerializer)
    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        """Square a count that didn't match: the extra cash goes in as a deposit, the missing cash out as a withdrawal,
        with the reason, so the cash in hand holds what was counted."""
        body = VoidSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        close = services.settle_close(self.get_object(), reason=body.validated_data["reason"], by=self.me)
        record(request, "drawer.settled", close, None, {"difference_paise": close.difference_paise, "move": close.settle_move_id, "reason": close.settle_reason})
        return Response(self.get_serializer(self.get_queryset().get(pk=close.pk)).data)


class CashView(GymViewMixin, APIView):
    """Each of the caller's branches' cash in hand: what it should hold now and today's count. The desk sees its own
    branches' cash only (never the bank: a shared account would show other branches' takings). Admins pass ?branch=."""

    roles = {"get": DESK}

    @extend_schema(parameters=[OpenApiParameter("branch", int)], responses=BranchCashSerializer(many=True))
    def get(self, request):
        branches = self.in_my_branches(Branch.objects.filter(gym=self.gym, is_active=True), "id").order_by("name")
        if (branch := int_param(request, "branch")) is not None:
            branches = branches.filter(pk=branch)
        return Response(BranchCashSerializer(services.cash_today(self.gym, branches), many=True).data)

