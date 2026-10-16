import hashlib

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.gyms.models import GymRole


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


class RefreshView(TokenRefreshView):
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
    branches = serializers.SerializerMethodField()

    class Meta:
        model = GymRole
        fields = ["gym", "gym_name", "role", "is_owner", "branches"]

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


class MeView(APIView):
    """Who is signed in, and which gyms and branches they can open. The app picks a gym and sends it as X-Gym."""

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        u = request.user
        roles = GymRole.objects.filter(user=u, is_active=True, gym__status__in=["trial", "active"]).select_related("gym")
        return Response(MeSerializer({"id": u.id, "name": u.name, "initials": u.initials, "email": u.email, "phone": u.phone, "roles": roles}).data)
