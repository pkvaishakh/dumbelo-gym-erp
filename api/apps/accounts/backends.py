from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError

from .models import User, normalize_phone


class EmailOrPhoneBackend(ModelBackend):
    """Sign in with an email (staff) or a mobile number (members), plus the password."""

    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        ident = (identifier or username or kwargs.get("email") or "").strip()
        if not ident or not password:
            return None
        try:
            if "@" in ident:
                user = User.objects.get(email__iexact=ident)
            else:
                user = User.objects.get(phone=normalize_phone(ident))
        except (User.DoesNotExist, ValidationError):
            User().set_password(password)  # same time either way, so a wrong identifier can't be told from a wrong password
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
