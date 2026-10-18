from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record
from apps.core.tenancy import ADMIN, DESK, GymViewMixin

from .. import services
from ..models import Refund
from ..serializers import RefundCreateSerializer, RefundSerializer, VoidSerializer


class RefundViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Money given back to members for plans they paid for. Admins give and void refunds; the desk sees its
    branches' refunds on a member's profile (`?member=`)."""

    serializer_class = RefundSerializer
    roles = {"list": DESK, "retrieve": DESK, "*": ADMIN}
    filterset_fields = ["member", "subscription", "voided"]

    def get_queryset(self):
        qs = Refund.objects.filter(gym=self.gym).select_related("member", "subscription__plan", "refunded_by__user")
        return self.in_my_branches(qs)

    @extend_schema(request=RefundCreateSerializer, responses={201: RefundSerializer})
    def create(self, request, *args, **kwargs):
        """Give money back for a plan: never more than was paid for it. It can end the plan today, or keep it."""
        body = RefundCreateSerializer(data=request.data, context=self.get_serializer_context())
        body.is_valid(raise_exception=True)
        d = body.validated_data
        r = services.refund(d["subscription"], amount_paise=d["amount_paise"], method=d["method"], reason=d["reason"], end_plan=d["end_plan"],
                            by=self.me, branch=d.get("branch"))
        record(request, "refund.given", r, None, {"member": r.member_id, "subscription": r.subscription_id, "amount_paise": r.amount_paise,
                                                  "method": r.method, "reason": r.reason, "ended_plan": r.ended_plan, "cancelled_plan": r.cancelled_plan})
        return Response(self.get_serializer(self.get_queryset().get(pk=r.pk)).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=VoidSerializer, responses=RefundSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """It was wrong: the money counts as paid again, and a plan it ended or cancelled is put back."""
        body = VoidSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        r = services.void_refund(self.get_object(), body.validated_data["reason"])
        record(request, "refund.voided", r, {"voided": False}, {"voided": True, "reason": r.void_reason})
        return Response(self.get_serializer(self.get_queryset().get(pk=r.pk)).data)
