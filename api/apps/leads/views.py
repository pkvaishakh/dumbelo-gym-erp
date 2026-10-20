from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import exceptions, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record
from apps.core.dumbelo import DumbeloViewMixin

from . import services
from .models import Lead
from .serializers import ConsoleLeadSerializer, LeadAskSerializer, LeadReceivedSerializer, LeadStatusSerializer


@extend_schema(tags=["leads"])
class LeadAskView(APIView):
    """A gym owner asking for a demo from the landing page. Open to anyone, so limited per address."""

    permission_classes = [AllowAny]
    # No sign-in is read: a visitor with an old token in the browser must not be refused, or signed out, for it.
    authentication_classes = []
    throttle_scope = "lead"

    def throttled(self, request, wait):
        # The form shows this as is, to a gym owner: not DRF's "Request was throttled. Expected available in 3540 seconds".
        # The wait still goes in the Retry-After header; only the words change.
        too_many = exceptions.Throttled(wait)
        too_many.detail = exceptions.ErrorDetail("We already have your request and will call you soon. To add something, try again in an hour.", code="throttled")
        raise too_many

    @extend_schema(request=LeadAskSerializer, responses={201: LeadReceivedSerializer})
    def post(self, request):
        ask = LeadAskSerializer(data=request.data)
        ask.is_valid(raise_exception=True)
        data = dict(ask.validated_data)
        if not data.pop("website", ""):
            services.take_lead(data)
        return Response({"received": True}, status=201)


@extend_schema(tags=["platform"])
class ConsoleLeadViewSet(DumbeloViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Gyms that asked for a demo, newest first. Filter with `?status=new`; search with `?q=`."""

    serializer_class = ConsoleLeadSerializer
    filterset_fields = ["status"]

    def get_queryset(self):
        qs = Lead.objects.select_related("status_by")
        q = self.request.query_params.get("q", "").strip()
        if len(q) >= 2:
            qs = qs.filter(Q(name__icontains=q) | Q(gym_name__icontains=q) | Q(city__icontains=q) | Q(phone__icontains=q))
        return qs

    @extend_schema(parameters=[OpenApiParameter("q", str, description="Part of a name, gym, city or phone number (2 or more characters)")])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=LeadStatusSerializer, responses=ConsoleLeadSerializer)
    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        lead = self.get_object()
        s = LeadStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = lead.status
        lead = services.set_status(lead, s.validated_data["status"], by=request.user)
        record(request, "lead.status", lead, {"status": before}, {"status": lead.status})
        return Response(ConsoleLeadSerializer(self.get_queryset().get(pk=lead.pk)).data)
