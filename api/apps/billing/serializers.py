from rest_framework import serializers

from .models import LAST_BILLING_DAY, BranchRequest, GymBilling, PriceList, Prices

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
    """A gym's Rackline plan as both its admins and the Console see it. `branches_in_use` and `current_prices`
    are filled in by the view (one query each)."""

    monthly_paise = serializers.IntegerField(read_only=True, help_text="Base fee + per-branch fee × quota, billed in advance")
    branches_in_use = serializers.IntegerField(read_only=True, help_text="Active branches")
    price_list = PriceListRefSerializer(read_only=True)
    whatsapp_mode = serializers.ChoiceField(choices=GymBilling.WHATSAPP_MODES, read_only=True)

    class Meta:
        model = GymBilling
        fields = [*Prices.FIELDS, "monthly_paise", "branch_quota", "branches_in_use", "billing_day", "whatsapp_mode", "paid_until", "price_list"]
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
