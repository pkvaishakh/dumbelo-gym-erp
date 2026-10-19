from django.utils import timezone
from rest_framework import serializers

from apps.gyms.models import Gym

from .models import LAST_BILLING_DAY, BranchRequest, GymBilling, Invoice, InvoiceLine, InvoicePayment, PriceList, Prices

MAX_PRICE_PAISE = 10_00_000_00  # ₹10 lakh: well past any real fee, so a slipped zero is caught


class PriceListSerializer(serializers.ModelSerializer):
    """A price list. `is_current` is the one in force today; `gym_count` how many gyms' plans were copied from it."""

    is_current = serializers.SerializerMethodField()
    gym_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PriceList
        fields = ["id", "active_from", *Prices.FIELDS, "note", "is_current", "gym_count", "created_at"]
        read_only_fields = fields

    def get_is_current(self, obj) -> bool:
        return obj.pk == self.context.get("current_id")


class PriceListCreateSerializer(serializers.ModelSerializer):
    """Add Price List: every price in paise. Lists are never edited, so a mistake is a new list from another day."""

    class Meta:
        model = PriceList
        fields = ["active_from", *Prices.FIELDS, "note"]
        extra_kwargs = {
            **{f: {"min_value": 0, "max_value": MAX_PRICE_PAISE} for f in Prices.FIELDS},
            "active_from": {"validators": []},  # a day already taken is the service's rule, in words for the person
        }


class PriceListRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = ["id", "active_from"]
        read_only_fields = fields


class PlanSerializer(serializers.ModelSerializer):
    """A gym's Dumbelo plan as both its admins and the Console see it. `branches_in_use`, `owed_paise` and
    `current_prices` are filled in by the view (one query each)."""

    monthly_paise = serializers.IntegerField(read_only=True, help_text="Base fee + per-branch fee × quota, billed in advance")
    branches_in_use = serializers.IntegerField(read_only=True, help_text="Active branches")
    price_list = PriceListRefSerializer(read_only=True)
    whatsapp_mode = serializers.ChoiceField(choices=GymBilling.WHATSAPP_MODES, read_only=True)
    owed_paise = serializers.IntegerField(read_only=True, help_text="What its open invoices still owe")

    class Meta:
        model = GymBilling
        fields = [*Prices.FIELDS, "monthly_paise", "branch_quota", "branches_in_use", "billing_day", "whatsapp_mode", "paid_until",
                  "owed_paise", "price_list"]
        read_only_fields = fields


class ConsolePlanSerializer(PlanSerializer):
    current_prices = PriceListRefSerializer(read_only=True, allow_null=True, help_text="Today's price list, when the gym isn't on it")

    class Meta(PlanSerializer.Meta):
        fields = PlanSerializer.Meta.fields + ["current_prices"]
        read_only_fields = fields


class PlanChangeSerializer(serializers.Serializer):
    branch_quota = serializers.IntegerField(min_value=1, max_value=200, required=False)
    billing_day = serializers.IntegerField(min_value=1, max_value=LAST_BILLING_DAY, required=False,
                                           help_text=f"1 to {LAST_BILLING_DAY}, so every month has one")
    whatsapp_mode = serializers.ChoiceField(choices=GymBilling.WHATSAPP_MODES, required=False)


class BranchAskSerializer(serializers.ModelSerializer):
    """A request for more branches, as the gym's admins see it."""

    status = serializers.ChoiceField(choices=BranchRequest.STATUS, read_only=True)
    asked_by_name = serializers.CharField(source="asked_by.name", read_only=True)
    days_charged = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = BranchRequest
        fields = ["id", "count", "note", "status", "asked_by_name", "created_at", "decided_at", "decline_reason",
                  "charged_from", "charged_to", "days_charged", "period_days", "rate_paise", "pro_rata_paise"]
        read_only_fields = fields


class BranchAskCreateSerializer(serializers.ModelSerializer):
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    class Meta:
        model = BranchRequest
        fields = ["count", "note"]
        extra_kwargs = {"count": {"min_value": 1, "max_value": BranchRequest.MAX}}


class ConsoleBranchAskSerializer(BranchAskSerializer):
    """A request in the Console: whose it is, who decided it and the gym's plan right now. All from the queryset."""

    gym = serializers.IntegerField(source="gym_id", read_only=True)
    gym_name = serializers.CharField(source="gym.name", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.name", read_only=True, allow_null=True)
    branch_quota = serializers.IntegerField(source="gym.billing.branch_quota", read_only=True)
    per_branch_paise = serializers.IntegerField(source="gym.billing.per_branch_paise", read_only=True)
    branches_in_use = serializers.IntegerField(read_only=True)

    class Meta(BranchAskSerializer.Meta):
        fields = BranchAskSerializer.Meta.fields + ["gym", "gym_name", "decided_by_name", "branch_quota", "per_branch_paise", "branches_in_use"]
        read_only_fields = fields


class DeclineSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200, help_text="Shown to the gym's admins", error_messages={
        "blank": "Say why, so the gym's admin knows", "required": "Say why, so the gym's admin knows"})


class GymPlanSerializer(PlanSerializer):
    """The gym's own view: its plan and its latest request for more branches (open, or how it was answered)."""

    last_request = BranchAskSerializer(read_only=True, allow_null=True)

    class Meta(PlanSerializer.Meta):
        fields = PlanSerializer.Meta.fields + ["last_request"]
        read_only_fields = fields


# Invoices

class InvoiceLineSerializer(serializers.ModelSerializer):
    kind = serializers.ChoiceField(choices=InvoiceLine.KINDS, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ["id", "kind", "description", "starts", "ends", "quantity", "rate_paise", "amount_paise", "tax_rate_bp", "tax_paise"]
        read_only_fields = fields


class InvoicePaymentSerializer(serializers.ModelSerializer):
    """A payment to Dumbelo and its receipt, as the gym's admins see it."""

    method = serializers.ChoiceField(choices=InvoicePayment.METHODS, read_only=True)

    class Meta:
        model = InvoicePayment
        fields = ["id", "receipt_number", "amount_paise", "method", "reference", "paid_on", "voided", "void_reason", "voided_at", "created_at"]
        read_only_fields = fields


class ConsoleInvoicePaymentSerializer(InvoicePaymentSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.name", read_only=True)
    voided_by_name = serializers.CharField(source="voided_by.name", read_only=True, allow_null=True)

    class Meta(InvoicePaymentSerializer.Meta):
        fields = InvoicePaymentSerializer.Meta.fields + ["recorded_by_name", "voided_by_name"]
        read_only_fields = fields


class InvoiceRowSerializer(serializers.ModelSerializer):
    """An invoice in a list. What's paid comes from the queryset (`with_paid`); `overdue` is an open invoice past
    its due day."""

    status = serializers.ChoiceField(choices=Invoice.STATUS, read_only=True)
    paid_paise = serializers.IntegerField(read_only=True, help_text="Leaving out voided payments")
    owed_paise = serializers.IntegerField(read_only=True, help_text="What's still to pay; 0 once paid or void")
    overdue = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ["id", "number", "period_from", "period_to", "issued_on", "due_on", "status", "subtotal_paise", "tax_paise",
                  "total_paise", "paid_paise", "owed_paise", "overdue"]
        read_only_fields = fields

    def get_overdue(self, obj) -> bool:
        return obj.status == Invoice.OPEN and obj.due_on < timezone.localdate()


class InvoiceDetailSerializer(InvoiceRowSerializer):
    """One invoice with its lines and payments, as the gym's admins see it and print it."""

    gym_name = serializers.CharField(source="gym.name", read_only=True)
    billing_email = serializers.CharField(source="gym.billing_email", read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    payments = InvoicePaymentSerializer(many=True, read_only=True)

    class Meta(InvoiceRowSerializer.Meta):
        fields = InvoiceRowSerializer.Meta.fields + ["gym_name", "billing_email", "void_reason", "voided_at", "lines", "payments"]
        read_only_fields = fields


class ConsoleInvoiceRowSerializer(InvoiceRowSerializer):
    gym = serializers.IntegerField(source="gym_id", read_only=True)
    gym_name = serializers.CharField(source="gym.name", read_only=True)

    class Meta(InvoiceRowSerializer.Meta):
        fields = InvoiceRowSerializer.Meta.fields + ["gym", "gym_name"]
        read_only_fields = fields


class ConsoleInvoiceSerializer(InvoiceDetailSerializer):
    gym = serializers.IntegerField(source="gym_id", read_only=True)
    voided_by_name = serializers.CharField(source="voided_by.name", read_only=True, allow_null=True)
    payments = ConsoleInvoicePaymentSerializer(many=True, read_only=True)

    class Meta(InvoiceDetailSerializer.Meta):
        fields = InvoiceDetailSerializer.Meta.fields + ["gym", "voided_by_name"]
        read_only_fields = fields


class RecordPaymentSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PRICE_PAISE * 10)
    method = serializers.ChoiceField(choices=InvoicePayment.METHODS)
    reference = serializers.CharField(max_length=80, required=False, allow_blank=True, default="", help_text="UTR, cheque or transaction number")
    paid_on = serializers.DateField(help_text="The day the money came in")


class InvoiceVoidSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200, help_text="Kept with it, and shown to the gym's admins", error_messages={
        "blank": "Say why, for the gym's history", "required": "Say why, for the gym's history"})


class ChargeSerializer(InvoiceLineSerializer):
    """A charge waiting for the gym's next invoice: added by a Dumbelo admin, or branches approved in the month."""

    gym = serializers.IntegerField(source="gym_id", read_only=True)
    added_by_name = serializers.CharField(source="added_by.name", read_only=True, allow_null=True)

    class Meta(InvoiceLineSerializer.Meta):
        fields = InvoiceLineSerializer.Meta.fields + ["gym", "added_by_name", "created_at"]
        read_only_fields = fields


class ChargeCreateSerializer(serializers.Serializer):
    """Add Charge. Setup fees take the gym's own price unless one is given; another charge needs its amount and what
    it's for."""

    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all())
    kind = serializers.ChoiceField(choices=[(k, label) for k, label in InvoiceLine.KINDS if k in InvoiceLine.CHARGES])
    quantity = serializers.IntegerField(min_value=1, max_value=50, default=1, help_text="Machines, for a machine setup")
    rate_paise = serializers.IntegerField(min_value=1, max_value=MAX_PRICE_PAISE, required=False, help_text="Each one; the gym's price if left out")
    description = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate(self, data):
        if data["kind"] == InvoiceLine.ADJUSTMENT:
            errors = {}
            if not data.get("rate_paise"):
                errors["rate_paise"] = "Enter the amount"
            if not data["description"].strip():
                errors["description"] = "Say what it's for, as the gym will read it"
            if errors:
                raise serializers.ValidationError(errors)
        return data
