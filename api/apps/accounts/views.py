import hashlib

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.core.errors import RuleBroken
from apps.core.dumbelo import is_dumbelo_admin
from apps.gyms.models import Gym, GymRole

from . import services
from .models import User, normalize_phone


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email (staff) or 10-digit mobile number (members)")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class TokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AccountThrottle(SimpleRateThrottle):
    """Sign-in tries per email or phone, so guessing one account's password is slow wherever it comes from."""

    scope = "login"

    def get_cache_key(self, request, view):
        ident = str(request.data.get("identifier", "")).strip().lower()
        if not ident:
            return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
        # Hashed: a safe cache key whatever was typed, and no emails or phone numbers sitting in the cache.
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
        user = authenticate(request, identifier=data.validated_data["identifier"], password=data.validated_data["password"])
        if not user:
            return Response({"error": {"code": "login_failed", "message": "That email, number or password is wrong"}}, status=401)
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
    name = serializers.CharField()
    initials = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    roles = RoleSerializer(many=True)
    is_dumbelo_admin = serializers.BooleanField(help_text="Runs the Console (/console): gyms, their admins, prices")


class MeEditSerializer(serializers.ModelSerializer):
    """A staff member's own name, sign-in email and mobile number."""

    name = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["name", "email", "phone"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Enter your name")
        return value.strip()

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Someone else signs in with this email")
        return value

    def validate_phone(self, value):
        try:
            value = normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])
        if value and User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Someone else has this mobile number")
        return value


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
    return MeSerializer({"id": u.id, "name": u.name, "initials": u.initials, "email": u.email, "phone": u.phone, "roles": roles,
                         "is_dumbelo_admin": is_dumbelo_admin(u)}).data


class MeView(APIView):
    """Who is signed in, and which gyms and branches they can open. The app picks a gym and sends it as X-Gym.
    Staff can change their own name, email and mobile number; a member's details are changed by the front desk.

    This is about the person, not a gym, so it answers whatever X-Gym says, suspended gyms included: their roles
    there carry `gym_status`, so the app can show the paused screen instead of failing on every call."""

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(me_data(request.user))

    @extend_schema(request=MeEditSerializer, responses=MeSerializer)
    def patch(self, request):
        if not request.user.email:  # members sign in with the phone number the desk keeps on their profile
            raise RuleBroken("details_by_desk", "Ask the front desk to change your details")
        edit = MeEditSerializer(request.user, data=request.data, partial=True)
        edit.is_valid(raise_exception=True)
        edit.save()
        return Response(me_data(request.user))


class PasswordView(APIView):
    """Change your own password. Every other device signed in as you is signed out; this one gets new tokens."""

    throttle_scope = "login"  # per account, like sign-in: guessing the current password must stay slow

    @extend_schema(request=PasswordChangeSerializer, responses=TokensSerializer)
    def post(self, request):
        data = PasswordChangeSerializer(data=request.data, context={"request": request})
        data.is_valid(raise_exception=True)
        v = data.validated_data
        return Response(services.change_own_password(request.user, v["current_password"], v["new_password"]))
