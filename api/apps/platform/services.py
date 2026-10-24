"""Dumbelo's side of a gym: opening one, pausing it, and the admin accounts that run it.

Dumbelo admins call these from the Console; `python manage.py create_gym` calls `create_gym` too, so a gym opened
from the command line is set up exactly like one opened in the Console.
"""
import zoneinfo
from dataclasses import dataclass
from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts import usernames
from apps.accounts.services import set_password
from apps.billing.services import open_plan
from apps.core.errors import RuleBroken
from apps.gyms.models import Branch, BranchSession, Gym, GymRole

User = get_user_model()

# A new branch needs opening hours before anyone can check in; the gym's admin renames or splits it in Branches.
FIRST_SESSION = ("All day", time(5), time(23))


@dataclass
class NewGym:
    gym: Gym
    owner: GymRole
    new_login: bool  # False: the owner already signed in to Dumbelo (another gym) and keeps their password


def find_login(username: str):
    return User.objects.filter(username=usernames.clean(username)).first() if username else None


def _login_for(*, existing_username: str = "", username: str = "", email: str = "", name: str = "",
               password: str | None = None) -> tuple[User, bool]:
    """The person's login: the one they already have (by its username), or a new one with the username given (or
    made from their email or name) and the first password they were told."""
    if existing_username:
        user = find_login(existing_username)
        if user is None:
            raise RuleBroken("no_login", f"No one signs in with @{usernames.clean(existing_username)}")
        if user.is_staff:  # Dumbelo's team sees inside gyms only through a support window
            raise RuleBroken("dumbelo_login", "That's a Dumbelo team login. Use the gym admin's own username.")
        return user, False
    if not name.strip():
        raise RuleBroken("name_needed", "They don't sign in to Dumbelo yet, so enter their name")
    if not password:
        raise RuleBroken("password_needed", "They don't sign in to Dumbelo yet, so set a first password for them")
    if username:
        try:
            username = usernames.validate(username)
        except DjangoValidationError as e:
            raise RuleBroken("username", e.messages[0])
    try:
        with transaction.atomic():
            return User.objects.create_user(username=username or None, email=email.strip() or None, password=password, name=name.strip()), True
    except IntegrityError:
        raise RuleBroken("username", "That username was just taken. Pick another.")


def check_timezone(name: str) -> str:
    if name not in zoneinfo.available_timezones():
        raise RuleBroken("bad_timezone", f"{name} isn't a time zone. Use one like Asia/Kolkata.")
    return name


@transaction.atomic
def create_gym(*, name: str, slug: str, timezone_name: str, branch: str, owner_existing_username: str = "",
               owner_username: str = "", owner_email: str = "", owner_name: str = "", owner_password: str | None = None,
               billing_email: str = "") -> NewGym:
    """A new gym on trial: its first branch, open all day until its admin sets the hours, its owner admin (the login
    they already have, or a new one), and its Dumbelo plan on today's prices with room for that one branch."""
    check_timezone(timezone_name)
    try:
        with transaction.atomic():
            gym = Gym.objects.create(name=name.strip(), slug=slug, timezone=timezone_name, billing_email=billing_email or owner_email.strip())
    except IntegrityError:
        raise RuleBroken("slug_taken", f"Another gym already uses {slug}. Pick another short name.")
    first = Branch.objects.create(gym=gym, name=branch.strip())
    BranchSession.objects.create(branch=first, name=FIRST_SESSION[0], starts=FIRST_SESSION[1], ends=FIRST_SESSION[2])
    open_plan(gym)
    user, new = _login_for(existing_username=owner_existing_username, username=owner_username, email=owner_email,
                           name=owner_name, password=owner_password)
    if not gym.billing_email and user.email:
        gym.billing_email = user.email
        gym.save(update_fields=["billing_email"])
    owner = GymRole.objects.create(user=user, gym=gym, role=GymRole.ADMIN, is_owner=True)
    return NewGym(gym, owner, new)


def _locked(gym: Gym) -> Gym:
    """The gym's row under a lock: status changes and owner changes for one gym happen one at a time."""
    return Gym.objects.select_for_update().get(pk=gym.pk)


@transaction.atomic
def suspend(gym: Gym, reason: str) -> Gym:
    """Pause the gym: its staff and members are refused, its admins keep their Dumbelo plan, nothing is sent."""
    gym = _locked(gym)
    if gym.is_suspended:
        raise RuleBroken("already_suspended", f"{gym.name} is already suspended")
    return _set_status(gym, Gym.SUSPENDED, reason)


@transaction.atomic
def activate(gym: Gym, reason: str) -> Gym:
    """Turn a suspended or trial gym on: everyone can use the app again from their next tap."""
    gym = _locked(gym)
    if gym.status == Gym.ACTIVE:
        raise RuleBroken("already_active", f"{gym.name} is already active")
    return _set_status(gym, Gym.ACTIVE, reason)


def _set_status(gym: Gym, status: str, reason: str) -> Gym:
    gym.status, gym.status_reason, gym.status_changed_at = status, reason.strip(), timezone.now()
    gym.save(update_fields=["status", "status_reason", "status_changed_at", "updated_at"])
    return gym


@transaction.atomic
def add_admin(gym: Gym, *, existing_username: str = "", username: str = "", email: str = "", name: str = "",
              password: str | None = None) -> tuple[GymRole, bool]:
    """Give someone an admin login to the gym: the one they already have, or a new one. An admin who was
    deactivated is turned back on instead."""
    user, new = _login_for(existing_username=existing_username, username=username, email=email, name=name, password=password)
    role = GymRole.objects.filter(user=user, gym=gym).first()
    if role is None:
        return GymRole.objects.create(user=user, gym=gym, role=GymRole.ADMIN), new
    if role.role != GymRole.ADMIN:
        raise RuleBroken("has_role", f"{user.name} is a {role.get_role_display().lower()} here. The gym's admin can make them an admin from Staff.")
    if role.is_active:
        raise RuleBroken("already_admin", f"{user.name} is already an admin of {gym.name}")
    role.is_active = True
    role.save(update_fields=["is_active", "updated_at"])
    return role, False


def reset_admin_password(role: GymRole, password: str) -> None:
    """A new password for a gym's admin who has lost theirs. They're signed out on every device."""
    if role.user.is_staff:
        raise RuleBroken("dumbelo_login", "That's a Dumbelo team login. They change their own password.")
    set_password(role.user, password)


@transaction.atomic
def deactivate_admin(role: GymRole) -> GymRole:
    """They can't open the gym any more. Never the owner: make someone else the owner first."""
    _locked(role.gym)
    role.refresh_from_db()
    if role.is_owner:
        raise RuleBroken("owner", "The account owner can't be deactivated. Make another admin the owner first.")
    if not role.is_active:
        raise RuleBroken("already_off", f"{role.user.name} is already deactivated")
    role.is_active = False
    role.save(update_fields=["is_active", "updated_at"])
    return role


@transaction.atomic
def reactivate_admin(role: GymRole) -> GymRole:
    role.refresh_from_db()
    if role.is_active:
        raise RuleBroken("already_on", f"{role.user.name} is already active")
    role.is_active = True
    role.save(update_fields=["is_active", "updated_at"])
    return role


@transaction.atomic
def make_owner(role: GymRole) -> GymRole | None:
    """The account owner handles Dumbelo billing and can't be removed. Returns who was the owner before."""
    _locked(role.gym)
    role.refresh_from_db()
    if not role.is_active:
        raise RuleBroken("not_active", f"{role.user.name} is deactivated. Turn them back on first.")
    if role.is_owner:
        raise RuleBroken("already_owner", f"{role.user.name} is already the account owner")
    before = GymRole.objects.filter(gym=role.gym_id, is_owner=True).select_related("user").first()
    if before is not None:  # one owner per gym: the old one steps down before the new one steps up
        before.is_owner = False
        before.save(update_fields=["is_owner", "updated_at"])
    role.is_owner = True
    role.save(update_fields=["is_owner", "updated_at"])
    return before
