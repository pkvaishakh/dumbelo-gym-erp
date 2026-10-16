"""Which gym a request is about, and who the caller is in it.

The web app sends `X-Gym: <slug>` on every call inside a gym. We check the signed-in user has an active role there
(or, for Rackline's own team, an open support window) and hang `request.gym` and `request.gym_role` on the request.
Every gym-scoped view filters by `request.gym`, and by `request.gym_role.branch_ids()` where branches matter.
"""
from rest_framework import exceptions, permissions

from apps.gyms.models import Gym, GymRole, SupportAccess


class SupportRole:
    """Stand-in role for Rackline support inside an open window: read-only, every branch."""

    role = "support"
    is_admin = False
    is_owner = False
    id = None

    def branch_ids(self):
        return None


def resolve_gym(request):
    if hasattr(request, "gym"):
        return request.gym, request.gym_role
    slug = request.headers.get("X-Gym")
    if not slug:
        raise exceptions.ValidationError({"X-Gym": ["Send the gym's slug in the X-Gym header"]})
    try:
        gym = Gym.objects.get(slug=slug)
    except Gym.DoesNotExist:
        raise exceptions.NotFound("No such gym")
    if gym.status == "suspended":
        raise exceptions.PermissionDenied("This gym's account is suspended")
    role = GymRole.objects.filter(user=request.user, gym=gym, is_active=True).first()
    if role is None:
        if request.user.is_staff and SupportAccess.open_for(gym):
            role = SupportRole()
        else:
            raise exceptions.NotFound("No such gym")  # same answer as a gym that doesn't exist: don't confirm it
    request.gym, request.gym_role = gym, role
    return gym, role


class InGym(permissions.BasePermission):
    """The caller has a role in the gym named by X-Gym. Views add `roles` rules on top (see RoleRules)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        gym, role = resolve_gym(request)
        if role.role == "support":
            return request.method in permissions.SAFE_METHODS
        rules = getattr(view, "roles", None)
        if not rules:
            return True
        action = getattr(view, "action", None) or request.method.lower()
        allowed = rules.get(action, rules.get("*", ()))
        return role.role in allowed


ALL = (GymRole.ADMIN, GymRole.RECEPTIONIST, GymRole.TRAINER, GymRole.MEMBER)
STAFF = (GymRole.ADMIN, GymRole.RECEPTIONIST, GymRole.TRAINER)
DESK = (GymRole.ADMIN, GymRole.RECEPTIONIST)
ADMIN = (GymRole.ADMIN,)


class _SchemaRole(SupportRole):
    role = GymRole.ADMIN
    is_admin = True


class GymViewMixin:
    """Base for views inside a gym. `roles` maps a viewset action (or "*") to the roles allowed to call it."""

    permission_classes = [InGym]
    roles = {"*": ADMIN}

    @property
    def gym(self):
        if getattr(self, "swagger_fake_view", False):  # building the OpenAPI schema: no request gym
            return None
        return self.request.gym

    @property
    def me(self):
        if getattr(self, "swagger_fake_view", False):
            return _SchemaRole()
        return self.request.gym_role

    def in_my_branches(self, qs, field="branch"):
        ids = self.me.branch_ids()
        return qs if ids is None else qs.filter(**{f"{field}__in": ids})
