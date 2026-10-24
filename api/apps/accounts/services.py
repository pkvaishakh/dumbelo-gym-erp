"""Logins: making one, finding the one someone already has, and who may change it (password, username, details).

One login per person across every gym. A gym may change a login only while it is that gym's alone."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.errors import RuleBroken
from apps.gyms.models import GymRole

from . import usernames
from .models import User


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


def shared_beyond(user, gym) -> bool:
    """True when this login isn't the gym's alone to change: Dumbelo's team, or someone with a role in another gym,
    even one switched off for now (it can be switched back on, and the login with it)."""
    return user.is_staff or GymRole.objects.filter(user=user).exclude(gym=gym).exists()


def check_login_is_this_gyms(role, what):
    """One login covers every gym the person belongs to, so only their own gym may change it on their behalf.
    Refuses for Dumbelo's team and for anyone with a role in another gym; they change it themselves."""
    if shared_beyond(role.user, role.gym):
        raise RuleBroken("shared_login", f"{role.user.name} also signs in to another gym, so only they can change their {what}")


def find_by_username(value, field="existing_username"):
    """The login someone already has, to add them to this gym as they are (password and all). Dumbelo's team
    never: they see inside a gym only through a support window."""
    user = User.objects.filter(username=usernames.clean(value)).first()
    if user is None:
        raise serializers.ValidationError({field: ["No one signs in with that username"]})
    if user.is_staff:
        raise serializers.ValidationError({field: ["That's a Dumbelo team login. Use the person's own username."]})
    if not user.is_active:
        raise serializers.ValidationError({field: ["That login is switched off"]})
    return user


def check_no_role_here(user, gym, field="existing_username"):
    """One role per person in a gym: someone already here is changed from their profile, not added again."""
    role = GymRole.objects.filter(user=user, gym=gym).first()
    if role is None:
        return
    if role.role == GymRole.MEMBER:
        message = f"{user.name} is a member here, and a person has one role in a gym"
    elif not role.is_active:
        message = f"{user.name} used to work here. Turn them back on from their profile."
    else:
        what = role.get_role_display().lower()
        message = f"{user.name} already works here as {'an' if what[0] in 'aeiou' else 'a'} {what}"
    raise serializers.ValidationError({field: [message]})


def new_login(*, username=None, password=None, name, email=None, phone=None, field="username"):
    """A new login. `username` is checked (taken, reserved, the wrong characters); left out, one is made from the
    email or name. Two people picking the same name at the same moment: the second is told it's taken."""
    if username:
        try:
            username = usernames.validate(username)
        except DjangoValidationError as e:
            raise serializers.ValidationError({field: e.messages})
    try:
        with transaction.atomic():
            return User.objects.create_user(username=username, password=password, name=name, email=email, phone=phone)
    except IntegrityError:
        raise serializers.ValidationError({field: ["That username was just taken. Pick another."]})


def reset_staff_password(role, password):
    """An admin sets a new password for a receptionist or trainer, who is then signed out everywhere.

    Not for admins (another admin could take over the account owner) or anyone who also works at another gym
    (one login covers every gym, so this gym's admin mustn't take it over): they change their own in the app.
    """
    if role.role == GymRole.ADMIN:
        raise RuleBroken("admin_password", "Admins change their own password, from More")
    check_login_is_this_gyms(role, "password")
    set_password(role.user, password)
