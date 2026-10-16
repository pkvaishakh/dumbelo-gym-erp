from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.audit.models import record
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.params import int_param
from apps.core.tenancy import ADMIN, ALL, DESK, STAFF, GymViewMixin
from apps.gyms.models import GymRole

from .models import STATUSES, Member, MemberNote, Offer, Payment, Plan, Subscription
from .serializers import (
    FreezeSerializer, MemberSelfSerializer, MemberSerializer, NoteSerializer, OfferSerializer, PasswordSerializer, PaymentCorrectSerializer,
    PaymentSerializer, PlanSerializer, SubscriptionSerializer, TrainerMemberSerializer, VoidSerializer, set_login,
)

class PlanViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Plans the gym sells. Admins set them up; everyone can see what's on sale."""

    serializer_class = PlanSerializer
    roles = {"list": ALL, "retrieve": ALL, "*": ADMIN}
    filterset_fields = ["kind", "on_sale"]

    def get_queryset(self):
        qs = Plan.objects.filter(gym=self.gym)
        return qs if self.me.role in (GymRole.ADMIN, "support") else qs.filter(on_sale=True)

    def perform_destroy(self, plan):
        if plan.subscriptions.exists():
            raise ValidationError("Members have bought this plan. Take it off sale instead.")
        plan.delete()


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("current", bool, description="Only offers that apply today")]))
class OfferViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Fixed offers. Only admins create them; the desk can only pick one that applies today."""

    serializer_class = OfferSerializer
    roles = {"list": DESK, "retrieve": DESK, "*": ADMIN}

    def get_queryset(self):
        qs = Offer.objects.filter(gym=self.gym).prefetch_related("plans").order_by("-starts")
        if self.request.query_params.get("current") or self.me.role == GymRole.RECEPTIONIST:
            today = clock.today(self.gym)
            qs = qs.filter(is_active=True, starts__lte=today, ends__gte=today)
        return qs

    def perform_destroy(self, offer):
        if offer.subscriptions.exists():
            raise ValidationError("This offer has been used. Switch it off instead.")
        offer.delete()


class MemberViewSet(GymViewMixin, viewsets.ModelViewSet):
    """Members. The desk and admins manage them in their branches; a trainer sees only their own members
    (no amounts); a member sees only themselves."""

    roles = {"list": ALL, "retrieve": ALL, "notes": STAFF, "destroy": ADMIN, "*": DESK}

    def get_serializer_class(self):
        if self.me.role == GymRole.MEMBER:
            return MemberSelfSerializer
        if self.me.role == GymRole.TRAINER:
            return TrainerMemberSerializer
        return MemberSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if hasattr(self.request, "gym"):
            ctx["today"] = clock.today(self.gym)
        return ctx

    def get_queryset(self):
        qs = Member.objects.filter(gym=self.gym).select_related("home_branch", "trainer__user", "user").with_totals()
        role = self.me.role
        if role == GymRole.MEMBER:
            return qs.filter(user=self.request.user)
        if role == GymRole.TRAINER:
            qs = qs.filter(trainer=self.me)
        else:
            qs = self.in_my_branches(qs, "home_branch")
        p = self.request.query_params
        if p.get("archived") != "true":
            qs = qs.filter(is_archived=False)
        if (branch := int_param(self.request, "branch")) is not None:
            qs = qs.filter(home_branch_id=branch)
        if (trainer := int_param(self.request, "trainer")) is not None:
            qs = qs.filter(trainer_id=trainer)
        if p.get("q"):
            q = p["q"].strip()
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(phone__contains=q))
        return qs

    @extend_schema(parameters=[
        OpenApiParameter("q", str, description="Name, member ID or phone"),
        OpenApiParameter("status", str, enum=STATUSES + ("attention",), description="attention: anything but active"),
        OpenApiParameter("branch", int), OpenApiParameter("trainer", int), OpenApiParameter("archived", bool),
    ])
    def list(self, request, *args, **kwargs):
        status = request.query_params.get("status")
        if not status:
            return super().list(request, *args, **kwargs)
        # Status comes from subscriptions, freezes and payments, so it's worked out in Python over the gym's members,
        # loaded with with_totals() in three queries. Fine to a few thousand members; move to a stored status updated
        # nightly if a gym outgrows it.
        today = clock.today(self.gym)
        wanted = (lambda s: s != "active") if status == "attention" else (lambda s: s == status)
        rows = [m for m in self.get_queryset() if wanted(m.status(today))]
        page = self.paginate_queryset(rows)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def perform_destroy(self, member):
        member.is_archived = True  # history stays: archive, never delete
        member.save(update_fields=["is_archived"])
        if member.user_id:
            GymRole.objects.filter(user=member.user, gym=self.gym, role=GymRole.MEMBER).update(is_active=False)
        record(self.request, "member.archived", member)

    @extend_schema(request=NoteSerializer, responses=NoteSerializer(many=True))
    @extend_schema(responses=NoteSerializer(many=True), request=NoteSerializer)
    @action(detail=True, methods=["get", "post"], pagination_class=None)
    def notes(self, request, pk=None):
        member = self.get_object()
        if request.method == "POST":
            s = NoteSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            s.save(member=member, author=self.me)
            return Response(s.data, status=201)
        return Response(NoteSerializer(member.notes.select_related("author__user"), many=True).data)

    @extend_schema(request=PasswordSerializer, responses=None)
    @action(detail=True, methods=["post"], url_path="set-login")
    def set_login(self, request, pk=None):
        """Set or reset the member's app password. They sign in with their phone number."""
        member = self.get_object()
        s = PasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        set_login(member, s.validated_data["password"])
        record(request, "member.login_set", member)
        return Response({"ok": True})

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Plans and payments for the member profile. Not for trainers: it has amounts."""
        if self.me.role == GymRole.TRAINER:
            raise RuleBroken("not_allowed", "Trainers don't see payment amounts")
        member = self.get_object()
        subs = member.subscriptions.select_related("plan", "offer").with_paid()
        pays = member.payments.select_related("taken_by__user")
        ctx = self.get_serializer_context()
        return Response({
            "subscriptions": SubscriptionSerializer(subs, many=True, context=ctx).data,
            "payments": PaymentSerializer(pays, many=True, context=ctx).data,
            "balance_paise": member.balance_paise(),
        })


class SubscriptionViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Selling a plan (new member or renewal), freezing, and cancelling. A renewal starts after the current plan ends."""

    serializer_class = SubscriptionSerializer
    roles = {"cancel": ADMIN, "*": DESK}
    filterset_fields = ["member", "plan"]

    def get_queryset(self):
        qs = Subscription.objects.filter(member__gym=self.gym).select_related("plan", "offer", "member").with_paid()
        return self.in_my_branches(qs, "member__home_branch")

    @extend_schema(request=FreezeSerializer, responses=SubscriptionSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def freeze(self, request, pk=None):
        """Pause a plan (travel, injury). The end date moves out by the days frozen."""
        sub = self.get_object()
        s = FreezeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        starts = s.validated_data.get("starts") or clock.today(self.gym)
        until = s.validated_data["until"]
        if sub.frozen_from:
            raise RuleBroken("already_frozen", "This plan is already frozen. Unfreeze it first.")
        if until < starts or starts > sub.ends or sub.ends < clock.today(self.gym):
            raise RuleBroken("freeze_invalid", "Choose dates inside the plan, ending after they start")
        before = {"ends": str(sub.ends)}
        sub.frozen_from, sub.frozen_until = starts, until
        sub.ends += timedelta(days=(until - starts).days + 1)
        sub.save()
        record(request, "subscription.frozen", sub, before, {"ends": str(sub.ends), "frozen_until": str(until)})
        return Response(self.get_serializer(sub).data)

    @extend_schema(request=None, responses=SubscriptionSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def unfreeze(self, request, pk=None):
        """End a freeze early; the days not used come off the end date again."""
        sub = self.get_object()
        if not sub.frozen_from:
            raise RuleBroken("not_frozen", "This plan isn't frozen")
        today = clock.today(self.gym)
        if sub.frozen_until and today <= sub.frozen_until:
            unused = (sub.frozen_until - max(today, sub.frozen_from)).days + (1 if today < sub.frozen_from else 0)
            sub.ends -= timedelta(days=max(0, unused))
        sub.frozen_from = sub.frozen_until = None
        sub.save()
        record(request, "subscription.unfrozen", sub)
        return Response(self.get_serializer(sub).data)

    @extend_schema(request=VoidSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        s = VoidSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if sub.paid_paise() > 0:
            raise RuleBroken("has_payments", "Void this plan's payments first")
        sub.cancelled = True
        sub.save(update_fields=["cancelled"])
        record(request, "subscription.cancelled", sub, None, {"reason": s.validated_data["reason"]})
        return Response(self.get_serializer(sub).data)


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("date", str, description="YYYY-MM-DD: payments taken that local day")]))
class PaymentViewSet(GymViewMixin, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Payments recorded at the desk. Receptionists record and see their branches; only admins correct or void."""

    roles = {"update": ADMIN, "partial_update": ADMIN, "void": ADMIN, "*": DESK}
    filterset_fields = ["member", "branch", "method", "voided"]

    def get_serializer_class(self):
        return PaymentCorrectSerializer if self.action in ("update", "partial_update") else PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.filter(gym=self.gym).select_related("member", "taken_by__user")
        qs = self.in_my_branches(qs)
        day = self.request.query_params.get("date")
        if day:
            start, end = clock.day_bounds(self.gym, clock.parse_date(day, None))
            qs = qs.filter(taken_at__gte=start, taken_at__lt=end)
        return qs

    def perform_update(self, serializer):
        p = serializer.instance
        if p.voided:
            raise RuleBroken("voided", "This payment was voided")
        before = {"amount_paise": p.amount_paise, "method": p.method, "note": p.note}
        reason = serializer.validated_data.pop("reason")
        p = serializer.save()
        record(self.request, "payment.corrected", p, before, {"amount_paise": p.amount_paise, "method": p.method, "note": p.note, "reason": reason})

    @extend_schema(request=VoidSerializer, responses=PaymentSerializer)
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        p = self.get_object()
        s = VoidSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if p.voided:
            raise RuleBroken("voided", "Already voided")
        p.voided, p.void_reason = True, s.validated_data["reason"]
        p.save(update_fields=["voided", "void_reason", "updated_at"])
        record(request, "payment.voided", p, {"voided": False}, {"voided": True, "reason": p.void_reason})
        return Response(PaymentSerializer(p, context=self.get_serializer_context()).data)

    @extend_schema(parameters=[OpenApiParameter("date", str), OpenApiParameter("branch", int)])
    @action(detail=False, methods=["get"])
    def collection(self, request):
        """Money taken on a day (today by default) in the caller's branches, by method — the desk's end-of-day count."""
        day = clock.parse_date(request.query_params.get("date"), clock.today(self.gym))
        start, end = clock.day_bounds(self.gym, day)
        qs = self.in_my_branches(Payment.objects.filter(gym=self.gym, voided=False, taken_at__gte=start, taken_at__lt=end))
        if (branch := int_param(request, "branch")) is not None:
            qs = qs.filter(branch_id=branch)
        by_method = {m: 0 for m, _ in Payment.METHODS}
        for row in qs.values("method").annotate(t=Sum("amount_paise")):
            by_method[row["method"]] = row["t"]
        return Response({"date": day, "total_paise": sum(by_method.values()), "count": qs.count(), "by_method": by_method})
