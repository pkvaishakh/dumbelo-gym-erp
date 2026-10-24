import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


def normalize_phone(value: str | None) -> str | None:
    """Indian mobile numbers stored as +91XXXXXXXXXX. Anything else is rejected."""
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) != 10:
        raise ValidationError("Enter a 10-digit mobile number")
    return "+91" + digits


def normalize_email(value: str | None) -> str | None:
    """Contact email as Django keeps it: trimmed, the domain lowercase. Empty is None."""
    return BaseUserManager.normalize_email((value or "").strip()) or None


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, password, **fields):
        from . import usernames

        fields["email"] = normalize_email(fields.get("email"))
        fields["phone"] = normalize_phone(fields.get("phone"))
        given = fields.get("username")
        fields["username"] = usernames.validate(given) if given else usernames.generate(fields["email"], fields.get("name"))
        user = self.model(**fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, password=None, **fields):
        fields.setdefault("is_staff", False)
        fields.setdefault("is_superuser", False)
        return self._create(password, username=username, **fields)

    def create_superuser(self, username=None, password=None, **fields):
        fields.update(is_staff=True, is_superuser=True)
        return self._create(password, username=username, **fields)

    def get_by_natural_key(self, username):
        from .usernames import clean

        return self.get(username=clean(username))


class User(AbstractBaseUser, PermissionsMixin):
    """One login for a person, across every gym they belong to. Everyone signs in with their username.

    Email and phone are contact details, not sign-in names: several logins can share one (a family's phone).
    `is_staff` means Dumbelo's own team (Django admin, support access), never gym staff:
    a person's role inside a gym lives on gyms.GymRole.
    """

    username = models.CharField(max_length=30, unique=True, help_text="Lowercase letters, numbers, . and _; how they sign in")
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=13, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(username=Lower("username")), name="username_is_lowercase"),
        ]

    def __str__(self):
        return self.name or self.username

    @property
    def initials(self):
        parts = self.name.replace("’", " ").split()
        return "".join(p[0] for p in parts[:2]).upper()
