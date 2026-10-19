import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
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


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, password, **fields):
        fields["email"] = self.normalize_email(fields.get("email")) or None
        fields["phone"] = normalize_phone(fields.get("phone"))
        if not fields["email"] and not fields["phone"]:
            raise ValueError("A user needs an email or a phone number")
        user = self.model(**fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **fields):
        fields.setdefault("is_staff", False)
        fields.setdefault("is_superuser", False)
        return self._create(password, email=email, **fields)

    def create_superuser(self, email, password, **fields):
        fields.update(is_staff=True, is_superuser=True)
        return self._create(password, email=email, **fields)


class User(AbstractBaseUser, PermissionsMixin):
    """One login for a person. Staff sign in with email, members with the phone number the desk registered.

    `is_staff` means Dumbelo's own team (Django admin, support access), never gym staff:
    a person's role inside a gym lives on gyms.GymRole.
    """

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=13, unique=True, null=True, blank=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False), name="user_has_email_or_phone"
            )
        ]

    def __str__(self):
        return self.name or self.email or self.phone or f"user {self.pk}"

    @property
    def initials(self):
        parts = self.name.replace("’", " ").split()
        return "".join(p[0] for p in parts[:2]).upper()
