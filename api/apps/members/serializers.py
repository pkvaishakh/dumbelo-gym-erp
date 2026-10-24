from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts import usernames
from apps.accounts.models import normalize_phone
from apps.accounts.services import find_by_username, new_login, set_password, shared_beyond
from apps.audit.models import record
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.finance.models import Account
from apps.gyms.models import Branch, GymRole

from . import services
from .models import STATUSES, Member, MemberNote, Offer, Payment, Plan, Refund, Subscription
from .pt_serializers import PTPlanSerializer, pt_plan


class CurrentPlanSerializer(serializers.Serializer):
    """The plan that lets the member in: their membership, or personal training at a gym that sells it alone."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    kind = serializers.ChoiceField(Plan.KINDS)
    starts = serializers.DateField()
    ends = serializers.DateField()
    frozen_from = serializers.DateField(allow_null=True)
    frozen_until = serializers.DateField(allow_null=True)


def gym_of(ctx):
    return ctx["request"].gym


@extend_schema_field(OpenApiTypes.INT)
class GymPK(serializers.PrimaryKeyRelatedField):
    """A foreign key that only accepts rows from the caller's gym, and with `branch_field`, from the caller's
    branches: another branch's row answers as if it didn't exist."""

    def __init__(self, model, gym_field="gym", extra=None, branch_field=None, **kw):
        self.model, self.gym_field, self.extra, self.branch_field = model, gym_field, extra or {}, branch_field
        super().__init__(**kw)

    def get_queryset(self):
        qs = self.model.objects.filter(**{self.gym_field: gym_of(self.context)}, **self.extra)
        ids = self.context["request"].gym_role.branch_ids() if self.branch_field else None
        if ids is None:
            return qs
        return qs.filter(pk__in=self.model.objects.filter(**{f"{self.branch_field}__in": ids}).values("pk"))  # once each, even many-to-many


class PlanSerializer(serializers.ModelSerializer):
    branches = GymPK(Branch, many=True, required=False, help_text="Empty means every branch")

    class Meta:
        model = Plan
        fields = ["id", "name", "kind", "months", "sessions", "price_paise", "includes", "on_sale", "branches"]

    def validate(self, data):
        kind = data.get("kind", getattr(self.instance, "kind", Plan.MEMBERSHIP))
        if not data.get("months", getattr(self.instance, "months", 0)):
            raise serializers.ValidationError({"months": "A membership plan needs a length" if kind == Plan.MEMBERSHIP
                                               else "Say how many months they have to use the sessions"})
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


class PaidBySerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=Payment.METHODS)
    amount_paise = serializers.IntegerField()


class SubscriptionSerializer(serializers.ModelSerializer):
    member = GymPK(Member, branch_field="home_branch")
    plan = GymPK(Plan, extra={"on_sale": True})
    offer = GymPK(Offer, required=False, allow_null=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    kind = serializers.ChoiceField(Plan.KINDS, source="plan.kind", read_only=True)
    offer_name = serializers.CharField(source="offer.name", read_only=True, default=None)
    trainer = GymPK(GymRole, required=False, allow_null=True, extra={"role": GymRole.TRAINER, "is_active": True}, branch_field="branches",
                    help_text="Personal training: who trains them. Left out, the member's trainer; they become the member's trainer")
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)
    sessions_used = serializers.IntegerField(read_only=True, source="used_total", default=0, help_text="Personal training sessions given")
    paid_paise = serializers.SerializerMethodField()
    refunded_paise = serializers.SerializerMethodField(help_text="Given back: the price and what was paid are both that much lower")
    paid_by = serializers.SerializerMethodField(help_text="What was paid, by method, voided payments left out")
    starts = serializers.DateField(required=False, help_text="Leave out: the day after the member's last plan ends, or today")
    ends = serializers.DateField(required=False, help_text="Leave out: from the plan's length. Admins only")

    class Meta:
        model = Subscription
        fields = ["id", "member", "plan", "plan_name", "kind", "offer", "offer_name", "starts", "ends", "list_price_paise", "price_paise", "paid_paise",
                  "refunded_paise", "paid_by", "frozen_from", "frozen_until", "cancelled", "sessions", "sessions_used", "trainer", "trainer_name"]
        read_only_fields = ["list_price_paise", "price_paise", "frozen_from", "frozen_until", "cancelled", "sessions"]

    def validate_ends(self, ends):
        if self.context["request"].gym_role.role != GymRole.ADMIN:
            raise serializers.ValidationError("Only an admin can set the end date. It follows the plan's length.")
        return ends

    def validate(self, data):
        if data.get("trainer") and data["plan"].kind != Plan.PT:
            raise serializers.ValidationError({"trainer": "Only personal training has a trainer"})
        return data

    def create(self, data):
        return services.sell(data["member"], data["plan"], by=self.context["request"].gym_role, offer=data.get("offer"), starts=data.get("starts"),
                             ends=data.get("ends"), trainer=data.get("trainer"))

    def get_paid_paise(self, sub) -> int:
        return sub.paid_paise()

    def get_refunded_paise(self, sub) -> int:
        return sub.refunded_paise()

    @extend_schema_field(PaidBySerializer(many=True))
    def get_paid_by(self, sub):
        """What was paid toward it, by method (cash ₹500, UPI ₹500), from the payments the list prefetches."""
        totals = {}
        for p in sub.payments.all():
            if not p.voided:
                totals[p.method] = totals.get(p.method, 0) + p.amount_paise
        return [{"method": m, "amount_paise": totals[m]} for m, _ in Payment.METHODS if m in totals]


class MemberSerializer(serializers.ModelSerializer):
    """What the desk and admins see. On create the desk can also sell the first plan, take the first payment,
    and give the member their app login: a new one (`username`, made up if left out, and `password`), or the one
    they already have at another gym (`existing_username`). After that, logins change through set-login."""

    home_branch = GymPK(Branch)
    trainer = GymPK(GymRole, required=False, allow_null=True, extra={"role": GymRole.TRAINER, "is_active": True}, branch_field="branches")
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)
    code = serializers.CharField(required=False, allow_blank=True)
    status = serializers.SerializerMethodField()
    balance_paise = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    pt = serializers.SerializerMethodField()
    has_login = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", required=False, allow_null=True, allow_blank=True, max_length=60,
                                     help_text="How they sign in to the app; null without a login. Set on create only")
    # create-only extras
    existing_username = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=60,
                                              help_text="Their login from another gym, instead of a new one")
    first_plan = GymPK(Plan, write_only=True, required=False, extra={"on_sale": True})
    offer = GymPK(Offer, write_only=True, required=False, allow_null=True)
    paid_paise = serializers.IntegerField(write_only=True, required=False, min_value=0)
    method = serializers.ChoiceField(Payment.METHODS, write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Member
        fields = [
            "id", "code", "name", "phone", "email", "home_branch", "trainer", "trainer_name", "goal", "joined_on",
            "device_user_id", "reminders_opted_out", "is_archived", "status", "balance_paise", "plan", "pt", "has_login",
            "username", "existing_username", "first_plan", "offer", "paid_paise", "method", "password",
        ]

    @extend_schema_field(serializers.ChoiceField(STATUSES))
    def get_status(self, m):
        return m.status(self.context.get("today"))

    def get_balance_paise(self, m) -> int:
        return m.balance_paise()

    @extend_schema_field(CurrentPlanSerializer(allow_null=True))
    def get_plan(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and {"id": sub.id, "name": sub.plan.name, "kind": sub.plan.kind, "starts": sub.starts, "ends": sub.ends,
                        "frozen_from": sub.frozen_from, "frozen_until": sub.frozen_until}

    @extend_schema_field(PTPlanSerializer(allow_null=True))
    def get_pt(self, m):
        return pt_plan(m, self.context.get("today"))

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
        if self.instance is None and data.get("user", {}).get("username") and not data.get("password") and not data.get("existing_username"):
            raise serializers.ValidationError({"password": "Set a password for their login"})
        return data

    @transaction.atomic
    def create(self, data):
        req = self.context["request"]
        plan, offer = data.pop("first_plan", None), data.pop("offer", None)
        paid, method = data.pop("paid_paise", 0), data.pop("method", None)
        password, existing = data.pop("password", None), data.pop("existing_username", "")
        username = data.pop("user", {}).get("username")
        if not data.get("code"):
            data["code"] = services.next_code(req.gym)
        member = Member.objects.create(gym=req.gym, **data)
        if password or existing:
            set_login(member, password, username=username, existing=existing)
        if plan:
            sub = services.sell(member, plan, by=req.gym_role, offer=offer)
            if paid:
                services.take_payment(member, paid, method, by=req.gym_role, subscription=sub)
        return member

    def update(self, member, data):
        for k in ("first_plan", "offer", "paid_paise", "method", "existing_username", "user"):
            data.pop(k, None)
        password = data.pop("password", None)
        was_archived = member.is_archived
        member = super().update(member, data)
        if password:
            set_login(member, password)
        if member.user_id:
            sync_login(member)
        if member.is_archived != was_archived:
            record(self.context["request"], "member.archived" if member.is_archived else "member.restored", member)
        return member


def owns_login(member) -> bool:
    """The member's login is this gym's member login alone: not shared with another gym, nor a staff login here
    (a receptionist must never reach a trainer's or admin's password through a member profile)."""
    user = member.user
    return not shared_beyond(user, member.gym) and not GymRole.objects.filter(user=user, gym=member.gym, role__in=GymRole.STAFF_ROLES).exists()


def sync_login(member):
    """Keep the member's role in step with their profile: switched off while archived, at their home branch. The
    login's phone follows the profile only when the login is this gym's alone; elsewhere it's someone else's to change."""
    role = GymRole.objects.filter(user=member.user, gym=member.gym, role=GymRole.MEMBER).first()
    if role is not None:
        if role.is_active == member.is_archived:
            role.is_active = not member.is_archived
            role.save(update_fields=["is_active", "updated_at"])
        role.branches.set([member.home_branch])
    if member.user.phone != member.phone and owns_login(member):
        member.user.phone = member.phone
        member.user.save(update_fields=["phone"])


@transaction.atomic
def set_login(member, password=None, *, username=None, existing=None):
    """The member's app login. Returns it and whether it was one they already had.

    - `existing`: the login they have from another gym, by its username. It's linked as it is: this gym never
      changes its password or username.
    - Already linked: a new password (they're signed out everywhere) and/or a new username, only while the login
      is this gym's member login alone; anyone else changes their own.
    - Otherwise a new login with `username` (made from their email or name if left out) and `password`.
    """
    gym = member.gym
    if existing:
        user = find_by_username(existing)
        taken = Member.objects.filter(gym=gym, user=user).exclude(pk=member.pk).first()
        if taken is not None:
            raise serializers.ValidationError({"existing_username": [f"@{user.username} is already {taken.name}'s login here"]})
    elif member.user_id:
        user = member.user
        if not owns_login(member):
            raise RuleBroken("shared_login", f"{member.name} also signs in to another gym or works here, so only they can change their login")
        if username and usernames.clean(username) != user.username:
            try:
                user.username = usernames.validate(username, exclude=user)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"username": e.messages})
            try:
                with transaction.atomic():
                    user.save(update_fields=["username"])
            except IntegrityError:
                raise serializers.ValidationError({"username": ["That username was just taken. Pick another."]})
        if password:
            set_password(user, password)
    else:
        if not password:
            raise serializers.ValidationError({"password": ["Set a password for their login"]})
        user = new_login(username=username, password=password, name=member.name, email=member.email or None, phone=member.phone)
    if member.user_id != user.id:
        member.user = user
        member.save(update_fields=["user"])
    GymRole.objects.get_or_create(user=user, gym=gym, defaults={"role": GymRole.MEMBER, "is_active": not member.is_archived})
    sync_login(member)
    return user, bool(existing)


class TrainerMemberSerializer(serializers.ModelSerializer):
    """What a trainer sees about their members: status and phone, and only whether payment is due — never amounts."""

    status = serializers.SerializerMethodField()
    payment_due = serializers.SerializerMethodField()
    plan_ends = serializers.SerializerMethodField()
    pt = serializers.SerializerMethodField()
    home_branch = serializers.CharField(source="home_branch.name")

    class Meta:
        model = Member
        fields = ["id", "code", "name", "phone", "goal", "home_branch", "status", "payment_due", "plan_ends", "pt"]

    @extend_schema_field(serializers.ChoiceField(STATUSES))
    def get_status(self, m):
        return m.status(self.context.get("today"))

    def get_payment_due(self, m) -> bool:
        return m.balance_paise() > 0

    @extend_schema_field(PTPlanSerializer(allow_null=True))
    def get_pt(self, m):
        return pt_plan(m, self.context.get("today"))

    @extend_schema_field(serializers.DateField(allow_null=True))
    def get_plan_ends(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and sub.ends


class TrainerTodaySerializer(serializers.Serializer):
    """A trainer's day on their Home. Never amounts."""

    class CheckedIn(serializers.Serializer):
        time = serializers.CharField(help_text="6:05 AM, in the gym's time zone")
        branch_name = serializers.CharField()

    class InToday(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()
        code = serializers.CharField()
        time = serializers.CharField()
        branch_name = serializers.CharField()

    class PTClient(serializers.Serializer):
        id = serializers.IntegerField(help_text="The member")
        name = serializers.CharField()
        code = serializers.CharField()
        pt = PTPlanSerializer()
        marked_today = serializers.BooleanField(help_text="Today's session is marked")

    checked_in = CheckedIn(allow_null=True, help_text="The trainer's own check-in today")
    statuses = serializers.DictField(child=serializers.IntegerField(), help_text="Their members counted by status: " + ", ".join(STATUSES))
    in_today = InToday(many=True, help_text="Their members who checked in today, latest first")
    pt = PTClient(many=True, help_text="Their members' personal training running now, fewest sessions left first")


class MemberSelfSerializer(TrainerMemberSerializer):
    """What a member sees about themselves: their plan, what they owe and their check-in code."""

    plan = serializers.SerializerMethodField()
    balance_paise = serializers.SerializerMethodField()
    trainer_name = serializers.CharField(source="trainer.user.name", read_only=True, default=None)

    class Meta(TrainerMemberSerializer.Meta):
        fields = TrainerMemberSerializer.Meta.fields + ["plan", "balance_paise", "trainer_name", "joined_on"]

    def get_plan(self, m):
        sub = m.current_subscription(self.context.get("today"))
        return sub and {"name": sub.plan.name, "kind": sub.plan.kind, "starts": sub.starts, "ends": sub.ends, "frozen_until": sub.frozen_until}

    def get_balance_paise(self, m):
        return m.balance_paise()


class NoteSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.user.name", read_only=True)

    class Meta:
        model = MemberNote
        fields = ["id", "text", "author", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    member = GymPK(Member, branch_field="home_branch")
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


class MemberPaymentSerializer(serializers.ModelSerializer):
    """A payment as the member who made it sees it: what, how, when and for which plan. No desk notes."""

    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True, default=None)
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)
    taken_by_name = serializers.CharField(source="taken_by.user.name", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "subscription", "plan_name", "amount_paise", "method", "branch_name", "taken_by_name", "taken_at"]
        read_only_fields = fields


class PaymentPartSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=Payment.METHODS)
    amount_paise = serializers.IntegerField(min_value=1)


class PaymentSplitSerializer(serializers.Serializer):
    """One amount paid more than one way: a payment is recorded for each part, together, with one receipt."""

    member = GymPK(Member, branch_field="home_branch")
    branch = GymPK(Branch, required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=200)
    parts = PaymentPartSerializer(many=True, min_length=2, max_length=len(Payment.METHODS))

    def validate_branch(self, branch):
        ids = self.context["request"].gym_role.branch_ids()
        if ids is not None and branch.id not in ids:
            raise serializers.ValidationError("You don't work at this branch")
        return branch

    def create(self, data):
        parts = [(p["method"], p["amount_paise"]) for p in data["parts"]]
        return services.take_split(data["member"], parts, by=self.context["request"].gym_role, branch=data.get("branch"), note=data.get("note", ""))


class PaymentCorrectSerializer(serializers.ModelSerializer):
    """Admins may correct the amount, method or note. The change is audited."""

    reason = serializers.CharField(write_only=True)

    class Meta:
        model = Payment
        fields = ["amount_paise", "method", "note", "reason"]

    @transaction.atomic  # for_money holds the account until the payment is saved
    def update(self, p, data):
        if "method" in data and data["method"] != p.method:  # cash corrected to UPI leaves the drawer for the bank
            data["account"] = Account.objects.for_money(p.branch_id, data["method"], on=clock.local(self.context["request"].gym, p.taken_at).date())
        return super().update(p, data)


class RefundSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.name", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True)
    refunded_by_name = serializers.CharField(source="refunded_by.user.name", read_only=True)

    class Meta:
        model = Refund
        fields = ["id", "member", "member_name", "subscription", "plan_name", "branch", "amount_paise", "method", "reason", "ended_plan", "cancelled_plan",
                  "refunded_by_name", "refunded_at", "voided", "void_reason"]
        read_only_fields = fields


class RefundCreateSerializer(serializers.Serializer):
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.none(), help_text="The plan the money was paid for")
    amount_paise = serializers.IntegerField(min_value=1, max_value=10_00_00_000_00)
    method = serializers.ChoiceField(choices=Payment.METHODS, help_text="How the money goes back: cash from the drawer, or from the bank")
    reason = serializers.CharField(max_length=200)
    end_plan = serializers.BooleanField(help_text="End the plan today (cancel it if it hasn't started), or keep it")
    branch = GymPK(Branch, required=False, help_text="Where it's given back; the member's home branch when left out")

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        req = self.context.get("request")
        if req is not None and hasattr(req, "gym"):
            self.fields["subscription"].queryset = Subscription.objects.filter(member__gym=req.gym)


class VoidSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200)


class SubscriptionCorrectSerializer(serializers.Serializer):
    """An admin's correction of a plan already sold. Send only what changes, and why."""

    plan = GymPK(Plan, required=False, help_text="Another plan: its price, and its length from the start date, unless given")
    offer = GymPK(Offer, required=False, allow_null=True, help_text="Another offer, or null for none: the price is worked out again")
    starts = serializers.DateField(required=False)
    ends = serializers.DateField(required=False)
    price_paise = serializers.IntegerField(required=False, min_value=0, help_text="What the member owes for it, set by hand")
    reason = serializers.CharField(max_length=200)


class FreezeSerializer(serializers.Serializer):
    starts = serializers.DateField(required=False)
    until = serializers.DateField()


class SetLoginSerializer(serializers.Serializer):
    """A new login (password, and a username or one made up), a new password or username for it, or
    `existing_username` to link the login they already have at another gym."""

    password = serializers.CharField(min_length=6, max_length=128, required=False, allow_blank=True)
    username = serializers.CharField(max_length=60, required=False, allow_blank=True)
    existing_username = serializers.CharField(max_length=60, required=False, allow_blank=True)

    def validate(self, data):
        if not any(data.get(k) for k in ("password", "username", "existing_username")):
            raise serializers.ValidationError({"password": "Set a password for their login"})
        return data


class LoginSetSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="How they sign in")
    name = serializers.CharField(help_text="Whose login it is: for a linked one, the name they gave Dumbelo")
    linked = serializers.BooleanField(help_text="It's the login they already had: they use their own password")


def today_ctx(view):
    return {"today": clock.today(view.request.gym)}
