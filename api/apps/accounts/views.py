import hashlib

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.core.errors import RuleBroken
from apps.core.dumbelo import is_dumbelo_admin
from apps.gyms.models import Gym, GymRole

from . import services, usernames
from .models import User, normalize_email, normalize_phone


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=60, help_text="Everyone signs in with their username; capitals don't matter")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class TokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AccountThrottle(SimpleRateThrottle):
    """Sign-in tries per username, so guessing one account's password is slow wherever it comes from."""

    scope = "login"

    def get_cache_key(self, request, view):
        ident = usernames.clean(str(request.data.get("username", "")))
        if not ident:
            return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
        # Hashed: a safe cache key whatever was typed, and no usernames sitting in the cache.
        return self.cache_format % {"scope": self.scope, "ident": hashlib.sha256(ident.encode()).hexdigest()}


class AddressThrottle(SimpleRateThrottle):
    """Sign-in tries per IP address. Looser: a whole gym's members can share one Wi-Fi address."""

    scope = "login_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountThrottle, AddressThrottle]

    @extend_schema(request=LoginSerializer, responses=TokensSerializer)
    def post(self, request):
        data = LoginSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = authenticate(request, username=data.validated_data["username"], password=data.validated_data["password"])
        if not user:
            return Response({"error": {"code": "login_failed", "message": "That username or password is wrong"}}, status=401)
        token = RefreshToken.for_user(user)
        return Response({"access": str(token.access_token), "refresh": str(token)})


class RefreshSerializer(TokenRefreshSerializer):
    """simplejwt 5.3 refreshes without asking whether the account is still there: a deleted or disabled login
    would keep getting access tokens, and the app would sit on 401s instead of going back to sign-in."""

    def validate(self, attrs):
        user_id = RefreshToken(attrs["refresh"]).payload.get(jwt_settings.USER_ID_CLAIM)
        if not User.objects.filter(**{jwt_settings.USER_ID_FIELD: user_id}, is_active=True).exists():
            raise AuthenticationFailed("Sign in again", code="user_inactive")
        return super().validate(attrs)


class RefreshView(TokenRefreshView):
    serializer_class = RefreshSerializer
    throttle_scope = "refresh"


class LogoutView(TokenBlacklistView):
    """Sign out: the refresh token stops working, so a copy of it can't be used later. The refresh token is the
    proof, so an expired access token mustn't block it."""

    authentication_classes = []
    throttle_scope = "refresh"


class BranchRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class RoleSerializer(serializers.ModelSerializer):
    gym = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    gym_name = serializers.CharField(source="gym.name", read_only=True)
    gym_status = serializers.ChoiceField(source="gym.status", choices=Gym.STATUS, read_only=True,
                                         help_text="suspended: the app shows its paused screen; only admins reach More")
    timezone = serializers.CharField(source="gym.timezone", read_only=True, help_text="The gym's time zone, like Asia/Kolkata: its days start and end there")
    month_days = serializers.IntegerField(source="gym.month_days", read_only=True, help_text="How long a plan's month runs: 0 for calendar months, else that many days")
    branches = serializers.SerializerMethodField()

    class Meta:
        model = GymRole
        fields = ["gym", "gym_name", "gym_status", "timezone", "month_days", "role", "is_owner", "branches"]

    @extend_schema_field(BranchRefSerializer(many=True))
    def get_branches(self, obj):
        rows = obj.gym.branches.filter(is_active=True) if obj.role == GymRole.ADMIN else obj.branches.filter(is_active=True)
        return [{"id": b.id, "name": b.name} for b in rows.order_by("name")]


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(help_text="How they sign in")
    name = serializers.CharField()
    initials = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    roles = RoleSerializer(many=True)
    is_dumbelo_admin = serializers.BooleanField(help_text="Runs the Console (/console): gyms, their admins, prices")


class MeEditSerializer(serializers.ModelSerializer):
    """A staff member's own username, name, email and mobile number. Email and phone are for contact (others may
    share them); the username must be free."""

    username = serializers.CharField(max_length=60)
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=254, required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "name", "email", "phone"]

    def validate_username(self, value):
        try:
            return usernames.validate(value, exclude=self.instance)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Enter your name")
        return value.strip()

    def validate_email(self, value):
        return normalize_email(value)

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, max_length=128, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, max_length=128, style={"input_type": "password"})

    def validate_new_password(self, value):
        try:
            validate_password(value, self.context["request"].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


def me_data(u):
    roles = GymRole.objects.filter(user=u, is_active=True).select_related("gym")
    return MeSerializer({"id": u.id, "username": u.username, "name": u.name, "initials": u.initials, "email": u.email, "phone": u.phone, "roles": roles,
                         "is_dumbelo_admin": is_dumbelo_admin(u)}).data


class MeView(APIView):
    """Who is signed in, and which gyms and branches they can open. The app picks a gym and sends it as X-Gym.
    Staff can change their own username, name, email and mobile number; a member's are changed by the front desk.

    This is about the person, not a gym, so it answers whatever X-Gym says, suspended gyms included: their roles
    there carry `gym_status`, so the app can show the paused screen instead of failing on every call."""

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(me_data(request.user))

    @extend_schema(request=MeEditSerializer, responses=MeSerializer)
    def patch(self, request):
        u = request.user
        if not (u.is_superuser or GymRole.objects.filter(user=u, role__in=GymRole.STAFF_ROLES).exists()):
            raise RuleBroken("details_by_desk", "Ask the front desk to change your details")  # a member's are the desk's
        edit = MeEditSerializer(u, data=request.data, partial=True)
        edit.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                edit.save()
        except IntegrityError:  # someone took the username between the check and the save
            raise serializers.ValidationError({"username": ["That username was just taken. Pick another."]})
        return Response(me_data(u))


class PasswordView(APIView):
    """Change your own password. Every other device signed in as you is signed out; this one gets new tokens."""

    throttle_scope = "login"  # per account, like sign-in: guessing the current password must stay slow

    @extend_schema(request=PasswordChangeSerializer, responses=TokensSerializer)
    def post(self, request):
        data = PasswordChangeSerializer(data=request.data, context={"request": request})
        data.is_valid(raise_exception=True)
        v = data.validated_data
        return Response(services.change_own_password(request.user, v["current_password"], v["new_password"]))


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="What was typed, as it would be stored: lowercase, no @")
    available = serializers.BooleanField()
    problem = serializers.CharField(allow_null=True, help_text="Why it can't be used, in words for the person typing")
    name = serializers.CharField(allow_null=True, help_text="Whose it is when it's taken, so the desk can see they're adding the right person")
    suggestions = serializers.ListField(child=serializers.CharField(), help_text="Free usernames, closest first; empty when it's available")


class UsernameThrottle(SimpleRateThrottle):
    """Per signed-in person: the check says whether a username exists, so it mustn't be a way to list them."""

    scope = "username"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.user.pk}


class UsernameCheckView(APIView):
    """Is this username free? If not, why, and some free ones made from what was typed, the email or the name.

    For gym staff (Add Staff, a member's app login, their own username in More) and Dumbelo admins (the Console).
    A taken username answers whose it is, so the desk adding someone who already signs in sees it's the right
    person; never for a Dumbelo team login."""

    throttle_classes = [UsernameThrottle]

    @extend_schema(parameters=[
        OpenApiParameter("username", str, description="What they typed; leave out for suggestions only"),
        OpenApiParameter("email", str, description="Suggestions start from the part before the @"),
        OpenApiParameter("name", str, description="Suggestions start from the name when there's no email"),
    ], responses=UsernameCheckSerializer)
    def get(self, request):
        u = request.user
        if not (is_dumbelo_admin(u) or GymRole.objects.filter(user=u, role__in=GymRole.STAFF_ROLES, is_active=True).exists()):
            raise PermissionDenied("Only gym staff can check usernames")
        p = request.query_params
        wanted = usernames.clean(p.get("username", ""))[:60]
        reason = usernames.problem(wanted) if wanted else "Choose a username"
        owner = None
        if reason is None:
            owner = User.objects.filter(username=wanted).exclude(pk=u.pk).first()
            reason = owner and "That username is taken"
        return Response(UsernameCheckSerializer({
            "username": wanted, "available": not reason, "problem": reason or None,
            "name": owner.name if owner is not None and not owner.is_staff else None,
            "suggestions": usernames.suggest(p.get("email"), p.get("name"), wanted) if reason else [],
        }).data)
