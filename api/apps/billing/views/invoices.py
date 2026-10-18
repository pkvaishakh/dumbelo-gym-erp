"""The Console's side of Rackline invoices: every gym's invoices, Record Payment, the voids and Add Charge.

Rackline admins only (`RacklineViewMixin`), no X-Gym. Every change is audited against its gym.
"""
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record
from apps.core.rackline import RacklineViewMixin

from .. import invoicing
from ..models import Invoice, InvoiceLine, InvoicePayment
from ..serializers import (
    ChargeCreateSerializer, ChargeSerializer, ConsoleInvoicePaymentSerializer, ConsoleInvoiceRowSerializer, ConsoleInvoiceSerializer,
    InvoiceVoidSerializer, RecordPaymentSerializer,
)


def _payment_audit(p: InvoicePayment) -> dict:
    return {"invoice": p.invoice.number, "receipt": p.receipt_number, "amount_paise": p.amount_paise, "method": p.method, "paid_on": p.paid_on.isoformat()}


@extend_schema(tags=["platform"])
class ConsoleInvoiceViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Every gym's Rackline invoices, newest first. Filter with `?gym=` or `?status=open`. Written by the billing-day
    job, never by hand; corrected by voiding."""

    filterset_fields = ["gym", "status"]

    def get_queryset(self):
        qs = Invoice.objects.with_paid().select_related("gym").order_by("-period_from", "-id")
        if self.action != "list":
            payments = InvoicePayment.objects.select_related("recorded_by", "voided_by").order_by("paid_on", "id")
            qs = qs.select_related("voided_by").prefetch_related("lines", Prefetch("payments", payments))
        return qs

    def get_serializer_class(self):
        return ConsoleInvoiceRowSerializer if self.action == "list" else ConsoleInvoiceSerializer

    def _detail(self, inv):
        return Response(ConsoleInvoiceSerializer(self.get_queryset().get(pk=inv.pk)).data)

    @extend_schema(request=RecordPaymentSerializer, responses=ConsoleInvoiceSerializer)
    @action(detail=True, methods=["post"])
    def payments(self, request, pk=None):
        """Record Payment: all or part of what it owes, never more. Paid in full, the gym's plan is paid until its
        last day."""
        inv = self.get_object()
        s = RecordPaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        pay = invoicing.record_payment(inv, by=request.user, **s.validated_data)
        record(request, "invoice.payment_recorded", pay, None, _payment_audit(pay), gym=inv.gym)
        return self._detail(inv)

    @extend_schema(request=InvoiceVoidSerializer, responses=ConsoleInvoiceSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Void Invoice, with a reason. Its payments are voided first; it keeps its number and lines."""
        inv = self.get_object()
        s = InvoiceVoidSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        before = {"status": inv.status}
        inv = invoicing.void_invoice(inv, reason=s.validated_data["reason"], by=request.user)
        record(request, "invoice.voided", inv, before, {"status": inv.status, "reason": inv.void_reason, "total_paise": inv.total_paise}, gym=inv.gym)
        return self._detail(inv)


@extend_schema(tags=["platform"])
class ConsoleInvoicePaymentViewSet(RacklineViewMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A payment to Rackline. Never deleted: Void Payment keeps it, with a reason, and the invoice owes it again."""

    serializer_class = ConsoleInvoicePaymentSerializer

    def get_queryset(self):
        return InvoicePayment.objects.select_related("invoice__gym", "recorded_by", "voided_by")

    @extend_schema(request=InvoiceVoidSerializer, responses=ConsoleInvoicePaymentSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        pay = self.get_object()
        s = InvoiceVoidSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        pay = invoicing.void_payment(pay, reason=s.validated_data["reason"], by=request.user)
        record(request, "invoice.payment_voided", pay, _payment_audit(pay), {"voided": True, "reason": pay.void_reason}, gym=pay.invoice.gym)
        return Response(ConsoleInvoicePaymentSerializer(self.get_queryset().get(pk=pay.pk)).data)


@extend_schema(tags=["platform"])
class ChargeViewSet(RacklineViewMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Charges waiting for a gym's next invoice (`?gym=`): setup fees and other charges added here, and the branches
    approved during the month. Add Charge adds one; one added by hand can be taken back until it's billed."""

    serializer_class = ChargeSerializer
    filterset_fields = ["gym"]

    def get_queryset(self):
        return InvoiceLine.objects.filter(invoice=None).select_related("added_by").order_by("created_at", "id")

    @extend_schema(request=ChargeCreateSerializer, responses={201: ChargeSerializer})
    def create(self, request, *args, **kwargs):
        s = ChargeCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = dict(s.validated_data)
        gym = v.pop("gym")
        line = invoicing.add_charge(gym, by=request.user, **v)
        record(request, "charge.added", line, None, _charge_audit(line), gym=gym)
        return Response(ChargeSerializer(self.get_queryset().get(pk=line.pk)).data, status=201)

    def destroy(self, request, *args, **kwargs):
        line = self.get_object()
        before = _charge_audit(line)
        invoicing.remove_charge(line)
        record(request, "charge.removed", line, before, None, gym=line.gym)
        return Response(status=204)


def _charge_audit(line: InvoiceLine) -> dict:
    return {"kind": line.kind, "description": line.description, "quantity": line.quantity, "amount_paise": line.amount_paise}
