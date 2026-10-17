from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core import clock
from apps.expenses.models import Expense
from apps.expenses.serializers import MAX_PAISE
from apps.gyms.models import Branch, GymRole
from apps.members.serializers import GymPK

from .models import Payslip, PayslipLine, SalaryItem, SalaryPayment, SalaryRule


class SalaryItemSerializer(serializers.ModelSerializer):
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)

    class Meta:
        model = SalaryItem
        fields = ["kind", "label", "amount_paise"]


class SalaryRuleSerializer(serializers.ModelSerializer):
    """How one person is paid. `items` are replaced as a whole on every save: the form sends the full list."""

    staff = GymPK(GymRole, extra={"role__in": GymRole.STAFF_ROLES})
    staff_name = serializers.CharField(source="staff.user.name", read_only=True)
    branch = GymPK(Branch)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    rate_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    items = SalaryItemSerializer(many=True, required=False)

    class Meta:
        model = SalaryRule
        fields = ["id", "staff", "staff_name", "branch", "branch_name", "pay_type", "rate_paise", "hours_per_day", "items"]

    def validate(self, data):
        if self.instance is not None and "staff" in data and data["staff"] != self.instance.staff:
            raise serializers.ValidationError({"staff": ["A salary belongs to one person. Set the other person's salary on their profile."]})
        if self.instance is None and SalaryRule.objects.filter(staff=data["staff"]).exists():
            raise serializers.ValidationError({"staff": ["They already have a salary. Change that one."]})
        pay_type = data.get("pay_type", getattr(self.instance, "pay_type", None))
        hours = data.get("hours_per_day", getattr(self.instance, "hours_per_day", 0))
        if pay_type == SalaryRule.HOURLY and not hours:
            raise serializers.ValidationError({"hours_per_day": ["Enter the hours of their shift"]})
        if len(data.get("items", [])) > 20:
            raise serializers.ValidationError({"items": ["Keep it to 20 allowances and deductions"]})
        return data

    def _save_items(self, rule, items):
        if items is None:
            return
        rule.items.all().delete()  # config, not history: each payslip keeps its own copy of the lines
        SalaryItem.objects.bulk_create([SalaryItem(rule=rule, **i) for i in items])

    def create(self, data):
        items = data.pop("items", [])
        rule = SalaryRule.objects.create(gym=self.context["request"].gym, **data)
        self._save_items(rule, items)
        return rule

    def update(self, rule, data):
        items = data.pop("items", None)
        rule = super().update(rule, data)
        self._save_items(rule, items)
        return rule


class PayslipLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayslipLine
        fields = ["id", "kind", "label", "amount_paise", "from_rule"]
        read_only_fields = fields


class SalaryPaymentSerializer(serializers.ModelSerializer):
    paid_by_name = serializers.CharField(source="paid_by.user.name", read_only=True)

    class Meta:
        model = SalaryPayment
        fields = ["id", "amount_paise", "method", "paid_on", "note", "paid_by_name"]
        read_only_fields = fields


class PayslipSerializer(serializers.ModelSerializer):
    """A row on the Payroll list. Paid amounts come from Payslip.objects.with_paid()."""

    staff_name = serializers.CharField(source="staff.user.name", read_only=True)
    staff_role = serializers.CharField(source="staff.role", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    paid_paise = serializers.SerializerMethodField()
    owed_paise = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = ["id", "staff", "staff_name", "staff_role", "branch", "branch_name", "month", "pay_type", "rate_paise", "hours_per_day",
                  "working_days", "days_present", "days_set_by_hand", "pay_paise", "additions_paise", "deductions_paise", "net_paise",
                  "paid_paise", "owed_paise", "payment_status", "status"]
        read_only_fields = fields  # payslips change only through the payroll actions

    def get_paid_paise(self, s) -> int:
        return s.paid_paise()

    def get_owed_paise(self, s) -> int:
        return s.net_paise - s.paid_paise()

    @extend_schema_field(serializers.ChoiceField(choices=["unpaid", "part", "paid"]))
    def get_payment_status(self, s) -> str:
        """unpaid, part or paid."""
        paid = s.paid_paise()
        if s.status == Payslip.APPROVED and s.net_paise == 0:
            return "paid"  # nothing to pay (deductions ate the month): settled, not waiting
        return "paid" if paid and paid >= s.net_paise else "part" if paid else "unpaid"


class PayslipDetailSerializer(PayslipSerializer):
    """One payslip with its breakdown and payments: the record screen and the printable slip."""

    lines = PayslipLineSerializer(many=True, read_only=True)
    payments = SalaryPaymentSerializer(many=True, read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.user.name", read_only=True, allow_null=True)
    staff_phone = serializers.CharField(source="staff.user.phone", read_only=True, allow_null=True)
    gym_name = serializers.CharField(source="gym.name", read_only=True)

    class Meta(PayslipSerializer.Meta):
        fields = PayslipSerializer.Meta.fields + ["lines", "payments", "approved_by_name", "approved_at", "staff_phone", "gym_name"]
        read_only_fields = fields


class MonthSerializer(serializers.Serializer):
    month = serializers.RegexField(r"^\d{4}-\d{2}$", error_messages={"invalid": "Use YYYY-MM"})

    def validate_month(self, v):
        return clock.parse_date(v + "-01", None, field="month")


class DaysSerializer(serializers.Serializer):
    days_present = serializers.IntegerField(min_value=0, max_value=31)


class LineSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=PayslipLine.KINDS)
    label = serializers.CharField(max_length=60)
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)


class RemoveLineSerializer(serializers.Serializer):
    line = serializers.IntegerField()


class PaySalarySerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    method = serializers.ChoiceField(choices=Expense.METHODS)
    paid_on = serializers.DateField(required=False)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_paid_on(self, v):
        if v > clock.today(self.context["request"].gym):
            raise serializers.ValidationError("Pick today or an earlier day")
        return v
