from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core import clock
from apps.finance.models import Account
from apps.gyms.models import Branch
from apps.members.serializers import GymPK

from .models import Expense, ExpenseDue, RecurringExpense

MAX_PAISE = 10_00_00_000_00  # ₹10 crore: far above any one bill, low enough to catch a slip of the keyboard


def paid_for(e: Expense) -> str | None:
    """"bill" or "salary" when the expense paid one. The list loads both with select_related (reverse one-to-ones),
    so hasattr answers from the row without a query."""
    return "bill" if hasattr(e, "due") else "salary" if hasattr(e, "salary_payment") else None


class ExpenseSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.none())
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    paid_for = serializers.SerializerMethodField(help_text="bill or salary when it paid one, so it is changed from there")

    class Meta:
        model = Expense
        fields = ["id", "branch", "branch_name", "category", "amount_paise", "method", "paid_to", "note", "spent_on", "paid_for"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            branches = Branch.objects.filter(gym=req.gym)
            ids = req.gym_role.branch_ids()  # the desk adds expenses for its own branches only
            self.fields["branch"].queryset = branches if ids is None else branches.filter(id__in=ids)

    def get_paid_for(self, e) -> str | None:
        return paid_for(e)

    def validate_amount_paise(self, v):
        if v <= 0:
            raise serializers.ValidationError("Enter an amount above zero")
        return v

    @transaction.atomic  # for_money holds the account until the expense is saved
    def create(self, data):
        req = self.context["request"]
        on = data.get("spent_on") or clock.today(req.gym)
        return Expense.objects.create(gym=req.gym, created_by=req.gym_role, account=Account.objects.for_money(data["branch"].id, data["method"], on=on), **data)

    @transaction.atomic
    def update(self, e, data):
        branch, method, on = data.get("branch", e.branch), data.get("method", e.method), data.get("spent_on", e.spent_on)
        # Paid another way, by another branch, or on another day: it comes out of that account (or none, before it was added).
        if branch != e.branch or method != e.method or on != e.spent_on:
            data["account"] = Account.objects.for_money(branch.id, method, on=on)
        return super().update(e, data)


class RecurringExpenseSerializer(serializers.ModelSerializer):
    branch = GymPK(Branch)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    next_due = serializers.DateField(read_only=True, allow_null=True, help_text="The next date not yet paid or skipped")
    dates_fixed = serializers.BooleanField(read_only=True, help_text="A date has been written, so starts and frequency can't change")

    class Meta:
        model = RecurringExpense
        fields = ["id", "branch", "branch_name", "name", "category", "amount_paise", "method", "paid_to", "note", "frequency", "starts", "ends",
                  "remind_days", "is_active", "next_due", "dates_fixed"]
        read_only_fields = ["is_active"]

    def validate(self, data):
        starts = data.get("starts", getattr(self.instance, "starts", None))
        ends = data.get("ends", getattr(self.instance, "ends", None))
        if starts and ends and ends < starts:
            raise serializers.ValidationError({"ends": ["Pick an end date on or after the first date it's due"]})
        if self.instance is not None and self.instance.dues.exists():
            for f in ("starts", "frequency"):
                if f in data and data[f] != getattr(self.instance, f):
                    raise serializers.ValidationError({f: ["Its dates are set once it's due. Stop this one and add a new one."]})
        return data

    def create(self, data):
        req = self.context["request"]
        return RecurringExpense.objects.create(gym=req.gym, created_by=req.gym_role, **data)


class ExpenseDueSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="recurring.name", read_only=True)
    category = serializers.CharField(source="recurring.category", read_only=True)
    method = serializers.CharField(source="recurring.method", read_only=True, help_text="How it is usually paid")
    paid_to = serializers.CharField(source="recurring.paid_to", read_only=True)
    branch = serializers.IntegerField(source="recurring.branch_id", read_only=True)
    branch_name = serializers.CharField(source="recurring.branch.name", read_only=True)
    paid_paise = serializers.IntegerField(source="expense.amount_paise", read_only=True, allow_null=True)
    paid_on = serializers.DateField(source="expense.spent_on", read_only=True, allow_null=True)
    state = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseDue
        fields = ["id", "recurring", "name", "category", "method", "paid_to", "branch", "branch_name", "due_on", "amount_paise", "status", "state",
                  "paid_paise", "paid_on"]
        read_only_fields = fields  # dues change only by paying or skipping

    @extend_schema_field(serializers.ChoiceField(choices=["overdue", "today", "soon", "later", "paid", "skipped"]))
    def get_state(self, due) -> str:
        """overdue, today, soon (inside its reminder days), later, paid or skipped."""
        if due.status != ExpenseDue.DUE:
            return due.status
        today = self.context["today"]
        return "overdue" if due.due_on < today else "today" if due.due_on == today else "soon" if due.remind_on <= today else "later"


class PayDueSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    method = serializers.ChoiceField(choices=Expense.METHODS)
    paid_on = serializers.DateField(required=False)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_paid_on(self, v):
        if v > clock.today(self.context["request"].gym):
            raise serializers.ValidationError("Pick today or an earlier day")
        return v
