"""The Console's side of billing: price lists, a gym's Rackline plan and the requests for more branches.

Rackline admins only (`RacklineViewMixin`), no X-Gym. Every change is audited, against its gym where it has one.
"""
from django.db.models import Count, OuterRef
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.queries import count_of
from apps.core.rackline import RacklineViewMixin
from apps.gyms.models import Branch, Gym

from .. import invoicing, services
from ..models import BranchRequest, GymBilling, PriceList
from ..serializers import (
    ConsoleBranchAskSerializer, ConsolePlanSerializer, DeclineSerializer, PlanChangeSerializer, PriceListCreateSerializer,
    PriceListSerializer,
)

GYM_ID = OpenApiParameter("gym_id", int, OpenApiParameter.PATH, description="The gym's id")


@extend_schema(tags=["platform"])
class PriceListViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Rackline's price lists, newest first. Added, never edited: gyms move to new prices one by one."""

    serializer_class = PriceListSerializer

    def get_queryset(self):
        return PriceList.objects.annotate(gym_count=Count("gyms")).order_by("-active_from")

    def get_serializer_context(self):
        current = PriceList.current()
        return {**super().get_serializer_context(), "current_id": current.pk if current else None}

    @extend_schema(request=PriceListCreateSerializer, responses={201: PriceListSerializer})
    def create(self, request, *args, **kwargs):
        s = PriceListCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = dict(s.validated_data)
        prices = services.add_price_list(active_from=v.pop("active_from"), note=v.pop("note", ""), prices=v, by=request.user)
        record(request, "price_list.added", prices, None, {"active_from": prices.active_from.isoformat(), **prices.prices()})
        return Response(PriceListSerializer(self.get_queryset().get(pk=prices.pk), context=self.get_serializer_context()).data, status=201)


def _audit_plan(plan: GymBilling) -> dict:
    return {"branch_quota": plan.branch_quota, "billing_day": plan.billing_day, "whatsapp_mode": plan.whatsapp_mode}


class _GymPlan(RacklineViewMixin, APIView):
    def gym(self) -> Gym:
        return get_object_or_404(Gym, pk=self.kwargs["gym_id"])

    def answer(self, gym: Gym) -> Response:
        plan = get_object_or_404(GymBilling.objects.select_related("price_list"), gym=gym)
        plan.branches_in_use = services.active_branches(gym)
        plan.owed_paise = invoicing.owed(gym)
        current = PriceList.current()
        plan.current_prices = current if current and current.pk != plan.price_list_id else None
        return Response(ConsolePlanSerializer(plan).data)


@extend_schema(tags=["platform"], parameters=[GYM_ID])
class GymPlanView(_GymPlan):
    """A gym's Rackline plan: its prices, branch quota, billing day and WhatsApp mode."""

    @extend_schema(responses=ConsolePlanSerializer)
    def get(self, request, gym_id):
        return self.answer(self.gym())

    @extend_schema(request=PlanChangeSerializer, responses=ConsolePlanSerializer)
    def patch(self, request, gym_id):
        """Set the quota (never below the branches open), the billing day or the WhatsApp mode."""
        gym = self.gym()
        s = PlanChangeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = _audit_plan(get_object_or_404(GymBilling, gym=gym))
        plan = services.change_plan(gym, **s.validated_data)
        if before != _audit_plan(plan):
            record(request, "billing.changed", plan, before, _audit_plan(plan), gym=gym)
        return self.answer(gym)


@extend_schema(tags=["platform"], parameters=[GYM_ID])
class GymPlanPricesView(_GymPlan):
    @extend_schema(request=None, responses=ConsolePlanSerializer)
    def post(self, request, gym_id):
        """Move to Current Prices: the gym's next invoice uses today's price list."""
        gym = self.gym()
        before = get_object_or_404(GymBilling, gym=gym)
        plan = services.move_to_current_prices(gym)
        record(request, "billing.prices_moved", plan, {"price_list": before.price_list_id, **before.prices()},
               {"price_list": plan.price_list_id, **plan.prices()}, gym=gym)
        return self.answer(gym)


@extend_schema(tags=["platform"])
class ConsoleBranchRequestViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Every gym's requests for more branches, to Approve or Decline. Filter with `?status=asked` or `?gym=`."""

    serializer_class = ConsoleBranchAskSerializer
    filterset_fields = ["status", "gym"]

    def get_queryset(self):
        in_use = count_of(Branch.objects.filter(gym=OuterRef("gym"), is_active=True))
        return (BranchRequest.objects.select_related("gym__billing", "asked_by", "decided_by")
                .annotate(branches_in_use=in_use).order_by("-created_at"))

    def _row(self, req):
        return Response(ConsoleBranchAskSerializer(self.get_queryset().get(pk=req.pk)).data)

    @extend_schema(request=None, responses=ConsoleBranchAskSerializer)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """The gym's quota goes up now; the rest of this billing month is charged on its next invoice."""
        req = self.get_object()
        quota = req.gym.billing.branch_quota
        req = services.approve(req, by=request.user)
        record(request, "branch_request.approved", req, {"branch_quota": quota},
               {"branch_quota": quota + req.count, "pro_rata_paise": req.pro_rata_paise}, gym=req.gym)
        return self._row(req)

    @extend_schema(request=DeclineSerializer, responses=ConsoleBranchAskSerializer)
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        req = self.get_object()
        s = DeclineSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        req = services.decline(req, by=request.user, reason=s.validated_data["reason"])
        record(request, "branch_request.declined", req, None, {"reason": req.decline_reason}, gym=req.gym)
        return self._row(req)
