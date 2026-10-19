"""Changing a login's password: the one rule book for a person changing their own and an admin resetting a staff member's."""
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.errors import RuleBroken
from apps.gyms.models import GymRole


@transaction.atomic
def set_password(user, password):
    """New password, and every device signed in with the old one is signed out (their refresh tokens stop working)."""
    user.set_password(password)
    user.save(update_fields=["password"])
    live = OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True)
    BlacklistedToken.objects.bulk_create([BlacklistedToken(token=t) for t in live], batch_size=500, ignore_conflicts=True)


def change_own_password(user, current, new):
    """The signed-in person changes their own password. Returns fresh tokens for this device."""
    if not user.check_password(current):
        raise RuleBroken("wrong_password", "That isn't your current password")
    set_password(user, new)
    token = RefreshToken.for_user(user)
    return {"access": str(token.access_token), "refresh": str(token)}


def check_login_is_this_gyms(role, what):
    """One login covers every gym the person works at, so only their own gym may change it on their behalf.
    Refuses for Dumbelo's team and for anyone with an active role in another gym; they change it themselves."""
    user = role.user
    if user.is_staff or GymRole.objects.filter(user=user, is_active=True).exclude(gym=role.gym).exists():
        raise RuleBroken("shared_login", f"{user.name} also signs in to another gym, so only they can change their {what}")


def reset_staff_password(role, password):
    """An admin sets a new password for a receptionist or trainer, who is then signed out everywhere.

    Not for admins (another admin could take over the account owner) or anyone who also works at another gym
    (one login covers every gym, so this gym's admin mustn't take it over): they change their own in the app.
    """
    if role.role == GymRole.ADMIN:
        raise RuleBroken("admin_password", "Admins change their own password, from More")
    check_login_is_this_gyms(role, "password")
    set_password(role.user, password)
