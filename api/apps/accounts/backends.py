from django.contrib.auth.backends import ModelBackend

from .models import User
from .usernames import clean


class UsernameBackend(ModelBackend):
    """Sign in with a username and password: one login per person, whichever gyms they belong to. Capitals don't
    matter. Email and phone aren't sign-in names, since several people can share one."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        name = clean(username)
        if not name or not password:
            return None
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            User().set_password(password)  # same time either way, so a wrong username can't be told from a wrong password
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
