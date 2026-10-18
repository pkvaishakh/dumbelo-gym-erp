"""The gym's own side of its Rackline plan: `/api/billing/plan/` and `/api/billing/branch-requests/`. Admins only."""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.tenancy import ADMIN, GymViewMixin

from .. import services
from ..models import BranchRequest, GymBilling
from ..serializers import BranchAskCreateSerializer, BranchAskSerializer, GymPlanSerializer


def gym_plan(gym) -> GymBilling:
    """The plan with what its screen shows next to it: branches open and the latest request. Three queries."""
    plan = get_object_or_404(GymBilling.objects.select_related("price_list"), gym=gym)
    plan.branches_in_use = services.active_branches(gym)
    plan.last_request = BranchRequest.objects.filter(gym=gym).select_related("asked_by").first()
    return plan


@extend_schema(tags=["billing"])
class RacklinePlanView(GymViewMixin, APIView):
    """What the gym pays Rackline and for how many branches. Open while the gym is suspended: its admins can still
    see their plan."""

    roles = {"*": ADMIN}
    open_when_suspended = True

    @extend_schema(responses=GymPlanSerializer)
    def get(self, request):
        return Response(GymPlanSerializer(gym_plan(self.gym)).data)


@extend_schema(tags=["billing"])
class BranchRequestViewSet(GymViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Add Branch to My Plan: the gym's admins ask Rackline for room for more branches. Rackline approves or declines."""

    serializer_class = BranchAskSerializer
    roles = {"*": ADMIN}

    def get_queryset(self):
        return BranchRequest.objects.filter(gym=self.gym).select_related("asked_by")

    @extend_schema(request=BranchAskCreateSerializer, responses={201: BranchAskSerializer})
    def create(self, request, *args, **kwargs):
        s = BranchAskCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        req = services.ask_for_branches(self.gym, count=s.validated_data["count"], note=s.validated_data["note"], by=request.user)
        record(request, "branch_request.asked", req, None, {"count": req.count, "note": req.note})
        return Response(BranchAskSerializer(req).data, status=201)
