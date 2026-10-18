import re

from rest_framework import serializers

from apps.core import clock
from apps.gyms.models import Branch
from apps.members.serializers import GymPK

from .models import Account, MoneyMove

MAX_PAISE = 100_00_00_000_00  # ₹100 crore: above any gym's account, low enough to catch a slip of the keyboard
IFSC = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
BANK_FIELDS = ("name", "bank_name", "account_number", "ifsc")


class AccountSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True, help_text="The bank account's name, or the branch's name and cash")
    branch = GymPK(Branch, required=False, allow_null=True, help_text="Cash in hand: the branch whose cash it is")
    branch_name = serializers.CharField(source="branch.name", read_only=True, allow_null=True)
    branches = GymPK(Branch, many=True, required=False, help_text="Bank accounts: the branches that use it. A branch using another account moves here")
    branch_names = serializers.SerializerMethodField()
    account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    opening_balance_paise = serializers.IntegerField(min_value=0, max_value=MAX_PAISE, required=False)
    balance_paise = serializers.IntegerField(read_only=True)
    collected_paise = serializers.IntegerField(read_only=True, help_text="Payments taken into it since it was added")
    spent_paise = serializers.IntegerField(read_only=True, help_text="Expenses paid from it since it was added")
    moved_in_paise = serializers.IntegerField(read_only=True)
    moved_out_paise = serializers.IntegerField(read_only=True)

    class Meta:
        model = Account
        fields = ["id", "kind", "label", "name", "branch", "branch_name", "branches", "branch_names", "bank_name", "account_number", "ifsc",
                  "opening_balance_paise", "opened_on", "is_active", "balance_paise", "collected_paise", "spent_paise", "moved_in_paise", "moved_out_paise"]
        read_only_fields = ["opened_on", "is_active"]

    def get_branch_names(self, a) -> list[str]:
        return [b.name for b in a.branches.all()]  # prefetched by services.listed

    def validate(self, data):
        a = self.instance
        for f in ("kind", "branch"):
            if a is not None and f in data and data[f] != getattr(a, f):
                raise serializers.ValidationError({f: ["This can't change once it's added. Add another account instead."]})
        kind = data.get("kind", getattr(a, "kind", None))
        if kind is None:
            raise serializers.ValidationError({"kind": ["Choose cash in hand or a bank account"]})
        return self._cash(data) if kind == Account.CASH else self._bank(data)

    def _cash(self, data):
        branch = data.get("branch", getattr(self.instance, "branch", None))
        if branch is None:
            raise serializers.ValidationError({"branch": ["Choose the branch whose cash this is"]})
        if data.get("branches"):
            raise serializers.ValidationError({"branches": ["Cash in hand belongs to its own branch"]})
        if self.instance is None and Account.objects.filter(kind=Account.CASH, branch=branch).exists():
            raise serializers.ValidationError({"branch": [f"{branch.name}'s cash is already set up"]})
        for f in BANK_FIELDS:
            data.pop(f, None)
        return data

    def _bank(self, data):
        if data.get("branch") is not None:
            raise serializers.ValidationError({"branch": ["A bank account is given to branches, not owned by one"]})
        value = lambda f: data[f] if f in data else getattr(self.instance, f, "")  # noqa: E731
        for f, message in (("name", "Name it, like HDFC current account"), ("bank_name", "Enter the bank's name"), ("account_number", "Enter the account number")):
            if not value(f).strip():
                raise serializers.ValidationError({f: [message]})
        number = re.sub(r"\s", "", value("account_number"))
        if not re.fullmatch(r"\d{6,20}", number):
            raise serializers.ValidationError({"account_number": ["Use the account number's digits, 6 to 20 of them"]})
        ifsc = value("ifsc").strip().upper()
        if ifsc and not IFSC.match(ifsc):
            raise serializers.ValidationError({"ifsc": ["Use the 11-character IFSC from a cheque, like HDFC0001234"]})
        clash = Account.objects.filter(gym=self.context["request"].gym, kind=Account.BANK, account_number=number)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError({"account_number": ["You've added this account already"]})
        data.update(name=value("name").strip(), bank_name=value("bank_name").strip(), account_number=number, ifsc=ifsc)
        return data

    def create(self, data):
        req = self.context["request"]
        return Account.objects.create(gym=req.gym, created_by=req.gym_role, opened_on=clock.today(req.gym), **data)


class BranchAccountSerializer(serializers.Serializer):
    branch = GymPK(Branch)
    account = GymPK(Account, allow_null=True, help_text="The bank account it uses from now on; null for none")


class MoneyMoveSerializer(serializers.ModelSerializer):
    from_account = GymPK(Account, required=False, allow_null=True)
    to_account = GymPK(Account, required=False, allow_null=True)
    from_name = serializers.CharField(source="from_account.label", read_only=True, allow_null=True)
    to_name = serializers.CharField(source="to_account.label", read_only=True, allow_null=True)
    from_kind = serializers.CharField(source="from_account.kind", read_only=True, allow_null=True)
    to_kind = serializers.CharField(source="to_account.kind", read_only=True, allow_null=True)
    amount_paise = serializers.IntegerField(min_value=1, max_value=MAX_PAISE)
    moved_on = serializers.DateField(required=False)
    created_by_name = serializers.CharField(source="created_by.user.name", read_only=True)

    class Meta:
        model = MoneyMove
        fields = ["id", "kind", "from_account", "from_name", "from_kind", "to_account", "to_name", "to_kind", "amount_paise", "moved_on", "note",
                  "created_by_name", "created_at", "voided", "void_reason"]
        read_only_fields = ["created_at", "voided", "void_reason"]

    def validate_moved_on(self, v):
        if v > clock.today(self.context["request"].gym):
            raise serializers.ValidationError("Pick today or an earlier day")
        return v
