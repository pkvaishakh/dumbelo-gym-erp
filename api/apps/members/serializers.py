from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.models import normalize_phone
from apps.core import clock
from apps.gyms.models import Branch, GymRole

from . import services
from .models import STATUSES, Member, MemberNote, Offer, Payment, Plan, Subscription

User = get_user_model()


class CurrentPlanSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    starts = serializers.DateField()
    ends = serializers.DateField()
    frozen_from = serializers.DateField(allow_null=True)
    frozen_until = serializers.DateField(allow_null=True)


def gym_of(ctx):
    return ctx["request"].gym


@extend_schema_field(OpenApiTypes.INT)
class GymPK(serializers.PrimaryKeyRelatedField):
    """A foreign key that only accepts rows from the caller's gym."""

    def __init__(self, model, gym_field="gym", extra=None, **kw):
        self.model, self.gym_field, self.extra = model, gym_field, extra or {}
        super().__init__(**kw)

    def get_queryset(self):
        return self.model.objects.filter(**{self.gym_field: gym_of(self.context)}, **self.extra)


class PlanSerializer(serializers.ModelSerializer):
    branches = GymPK(Branch, many=True, required=False, help_text="Empty means every branch")

    class Meta:
        model = Plan
        fields = ["id", "name", "kind", "months", "sessions", "price_paise", "includes", "on_sale", "branches"]

    def validate(self, data):
        kind = data.get("kind", getattr(self.instance, "kind", Plan.MEMBERSHIP))
        if kind == Plan.MEMBERSHIP and not data.get("months", getattr(self.instance, "months", 0)):
            raise serializers.ValidationError({"months": "A membership plan needs a length"})
        if kind == Plan.PT and not data.get("sessions", getattr(self.instance, "sessions", 0)):
            raise serializers.ValidationError({"sessions": "A personal training plan needs a number of sessions"})
        name = data.get("name")
        if name:
            clash = Plan.objects.filter(gym=gym_of(self.context), name__iexact=name)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError({"name": f"There is already a plan called {name}"})
        return data

    def create(self, data):
        branches = data.pop("branches", [])
        plan = Plan.objects.create(gym=gym_of(self.context), **data)
        plan.branches.set(branches)
        return plan


class OfferSerializer(serializers.ModelSerializer):
    plans = GymPK(Plan, many=True, required=False, help_text="Empty means every plan")
    branches = GymPK(Branch, many=True, required=False, help_text="Empty means every branch")

    class Meta:
        model = Offer
        fields = ["id", "name", "percent_off", "amount_off_paise", "plans", "branches", "starts", "ends", "is_active"]

    def validate(self, data):
        pct = data.get("percent_off", getattr(self.instance, "percent_off", None))
        amt = data.get("amount_off_paise", getattr(self.instance, "amount_off_paise", None))
        if (pct is None) == (amt is None):
            raise serializers.ValidationError("Give either a percentage or an amount off, not both")
        if pct is not None and not 1 <= pct <= 100:
            raise serializers.ValidationError({"percent_off": "Between 1 and 100"})
        starts = data.get("starts", getattr(self.instance, "starts", None))
        ends = data.get("ends", getattr(self.instance, "ends", None))
        if starts and ends and ends < starts:
            raise serializers.ValidationError({"ends": "The offer must end after it starts"})
        return data

    def create(self, data):
        plans, branches = data.pop("plans", []), data.pop("branches", [])
        offer = Offer.objects.create(gym=gym_of(self.context), **data)
        offer.plans.set(plans)
        offer.branches.set(branches)
        return offer


class SubscriptionSerializer(serializers.ModelSerializer):
    member = GymPK(Member)
    plan = GymPK(Plan, extra={"on_sale": True})
    offer = GymPK(Offer, required=False, allow_null=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    offer_name = serializers.CharField(source="offer.name", read_only=True, default=None)
    paid_paise = serializers.SerializerMethodField()
    starts = serializers.DateField(required=False)

    class Meta:
        model = Subscription
        fields = ["id", "member", "plan", "plan_name", "offer", "offer_name", "starts", "ends", "list_price_paise", "price_paise", "paid_paise", "frozen_from", "frozen_until", "cancelled"]
        read_only_fields = ["ends", "list_price_paise", "price_paise", "frozen_from", "frozen_until", "cancelled"]

    def create(self, data):
        return services.sell(data["member"], data["plan"], by=self.context["request"].gym_role, offer=data.get("offer"), starts=data.get("starts"))

    def get_paid_paise(self, sub) -> int:
        return sub.paid_paise()


class MemberSerializer(serializers.ModelSerializer):
    """What the desk and admins see. On create the desk can also sell the first plan, take the first payment,
    and set the member's app login (their phone + a password)."""

    home_branch = GymPK(Branch)
    trainer = GymPK(GymRole, required=False, allow_null=True, extra={"role": GymRole.TRAINER, "is_active": True})
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)
    code = serializers.CharField(required=False, allow_blank=True)
    status = serializers.SerializerMethodField()
    balance_paise = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    has_login = serializers.SerializerMethodField()
    # create-only extras
    first_plan = GymPK(Plan, write_only=True, required=False, extra={"on_sale": True})
    offer = GymPK(Offer, write_only=True, required=False, allow_null=True)
    paid_paise = serializers.IntegerField(write_only=True, required=False, min_value=0)
    method = serializers.ChoiceField(Payment.METHODS, write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Member
        fields = [
            "id", "code", "name", "phone", "email", "home_branch", "trainer", "trainer_name", "goal", "joined_on",
            "device_user_id", "reminders_opted_out", "is_archived", "status", "balance_paise", "plan", "has_login",
            "first_plan", "offer", "paid_paise", "method", "password",
        ]

    @extend_schema_field(serializers.ChoiceField(STATUSES))
    def get_status(self, m):
        return m.status(self.context.get("today"))

    def get_balance_paise(self, m) -> int:
        return m.balance_paise()

    @extend_schema_field(CurrentPlanSerializer(allow_null=True))
    def get_plan(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and {"id": sub.id, "name": sub.plan.name, "starts": sub.starts, "ends": sub.ends, "frozen_from": sub.frozen_from, "frozen_until": sub.frozen_until}

    def get_has_login(self, m) -> bool:
        return m.user_id is not None

    def validate_phone(self, value):
        try:
            phone = normalize_phone(value)
        except Exception:
            raise serializers.ValidationError("Enter a 10-digit mobile number")
        clash = Member.objects.filter(gym=gym_of(self.context), phone=phone)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("Another member has this number")
        return phone

    def validate_home_branch(self, branch):
        ids = self.context["request"].gym_role.branch_ids()
        if ids is not None and branch.id not in ids:
            raise serializers.ValidationError("You don't work at this branch")
        return branch

    def validate(self, data):
        if data.get("paid_paise") and not data.get("method"):
            raise serializers.ValidationError({"method": "How did they pay?"})
        if (data.get("paid_paise") or data.get("offer")) and not data.get("first_plan"):
            raise serializers.ValidationError({"first_plan": "Choose a plan first"})
        return data

    @transaction.atomic
    def create(self, data):
        req = self.context["request"]
        plan, offer = data.pop("first_plan", None), data.pop("offer", None)
        paid, method = data.pop("paid_paise", 0), data.pop("method", None)
        password = data.pop("password", None)
        if not data.get("code"):
            data["code"] = services.next_code(req.gym)
        member = Member.objects.create(gym=req.gym, **data)
        if password:
            set_login(member, password)
        if plan:
            sub = services.sell(member, plan, by=req.gym_role, offer=offer)
            if paid:
                services.take_payment(member, paid, method, by=req.gym_role, subscription=sub)
        return member

    def update(self, member, data):
        for k in ("first_plan", "offer", "paid_paise", "method"):
            data.pop(k, None)
        password = data.pop("password", None)
        member = super().update(member, data)
        if password:
            set_login(member, password)
        if member.user_id and member.user.phone != member.phone:
            member.user.phone = member.phone
            member.user.save(update_fields=["phone"])
        return member


@transaction.atomic
def set_login(member, password):
    """The desk sets the member's app password. Their login is their phone number."""
    user = member.user or User.objects.filter(phone=member.phone).first()
    if user is None:
        user = User.objects.create_user(phone=member.phone, password=password, name=member.name)
    else:
        user.set_password(password)
        user.save()
    if member.user_id != user.id:
        member.user = user
        member.save(update_fields=["user"])
    role, _ = GymRole.objects.get_or_create(user=user, gym=member.gym, defaults={"role": GymRole.MEMBER})
    if role.role == GymRole.MEMBER:
        role.is_active = not member.is_archived
        role.save()
        role.branches.set([member.home_branch])


class TrainerMemberSerializer(serializers.ModelSerializer):
    """What a trainer sees about their members: status and phone, and only whether payment is due — never amounts."""

    status = serializers.SerializerMethodField()
    payment_due = serializers.SerializerMethodField()
    plan_ends = serializers.SerializerMethodField()
    home_branch = serializers.CharField(source="home_branch.name")

    class Meta:
        model = Member
        fields = ["id", "code", "name", "phone", "goal", "home_branch", "status", "payment_due", "plan_ends"]

    @extend_schema_field(serializers.ChoiceField(STATUSES))
    def get_status(self, m):
        return m.status(self.context.get("today"))

    def get_payment_due(self, m) -> bool:
        return m.balance_paise() > 0

    @extend_schema_field(serializers.DateField(allow_null=True))
    def get_plan_ends(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and sub.ends


class MemberSelfSerializer(TrainerMemberSerializer):
    """What a member sees about themselves: their plan, what they owe and their check-in code."""

    plan = serializers.SerializerMethodField()
    balance_paise = serializers.SerializerMethodField()
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)

    class Meta(TrainerMemberSerializer.Meta):
        fields = TrainerMemberSerializer.Meta.fields + ["plan", "balance_paise", "trainer_name", "joined_on"]

    def get_plan(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and {"name": sub.plan.name, "starts": sub.starts, "ends": sub.ends, "frozen_until": sub.frozen_until}

    def get_balance_paise(self, m):
        return m.balance_paise()


class NoteSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.user.name", read_only=True)

    class Meta:
        model = MemberNote
        fields = ["id", "text", "author", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    member = GymPK(Member)
    member_name = serializers.CharField(source="member.name", read_only=True)
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.none(), required=False, allow_null=True)
    branch = GymPK(Branch, required=False)
    taken_by_name = serializers.CharField(source="taken_by.user.name", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "member", "member_name", "subscription", "branch", "amount_paise", "method", "note", "taken_by_name", "taken_at", "voided", "void_reason"]
        read_only_fields = ["taken_at", "voided", "void_reason"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            self.fields["subscription"].queryset = Subscription.objects.filter(member__gym=req.gym)

    def validate(self, data):
        sub, member = data.get("subscription"), data.get("member")
        if sub and member and sub.member_id != member.id:
            raise serializers.ValidationError({"subscription": "That plan belongs to someone else"})
        branch = data.get("branch")
        ids = self.context["request"].gym_role.branch_ids()
        if branch and ids is not None and branch.id not in ids:
            raise serializers.ValidationError({"branch": "You don't work at this branch"})
        return data

    def create(self, data):
        return services.take_payment(
            data["member"], data["amount_paise"], data["method"], by=self.context["request"].gym_role,
            branch=data.get("branch"), subscription=data.get("subscription"), note=data.get("note", ""),
        )


class PaymentCorrectSerializer(serializers.ModelSerializer):
    """Admins may correct the amount, method or note. The change is audited."""

    reason = serializers.CharField(write_only=True)

    class Meta:
        model = Payment
        fields = ["amount_paise", "method", "note", "reason"]


class VoidSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200)


class FreezeSerializer(serializers.Serializer):
    starts = serializers.DateField(required=False)
    until = serializers.DateField()


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6)


def today_ctx(view):
    return {"today": clock.today(view.request.gym)}
