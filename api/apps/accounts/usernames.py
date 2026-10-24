"""Usernames: how everyone signs in. One per person across every gym, chosen like an Instagram handle.

Stored lowercase, so `Ravi.K` and `ravi.k` are the same username. Email and phone are only contact details: a family
can share one phone, and each of them still has their own username.
"""
import re
import secrets
import unicodedata

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

MIN, MAX = 3, 30
ALLOWED = re.compile(r"^[a-z0-9._]+$")
# Names people could mistake for Dumbelo or the app itself.
RESERVED = frozenset({
    "admin", "administrator", "root", "system", "staff", "support", "help", "dumbelo", "console", "api", "app", "www",
    "login", "logout", "signin", "signup", "me", "settings", "null", "undefined", "owner", "gym", "member", "trainer",
    "receptionist", "desk",
})


def clean(value: str | None) -> str:
    """What was typed, as it is stored: no spaces, no leading @, lowercase."""
    return (value or "").strip().lstrip("@").lower()


def problem(value: str) -> str | None:
    """Why `value` (already cleaned) can't be a username, in words for the person typing it. None when it can."""
    if len(value) < MIN:
        return f"Use at least {MIN} characters"
    if len(value) > MAX:
        return f"Use {MAX} characters or fewer"
    if not ALLOWED.match(value):
        return "Use only letters, numbers, full stops and underscores"
    if value.startswith(".") or value.endswith(".") or ".." in value:
        return "A username can't start or end with a full stop, or have two in a row"
    if value.isdigit():
        return "Add a letter: a username can't be only numbers"
    if value in RESERVED:
        return "That username isn't available"
    return None


def is_taken(value: str, exclude=None) -> bool:
    qs = get_user_model().objects.filter(username=value)
    if exclude is not None:
        qs = qs.exclude(pk=exclude.pk)
    return qs.exists()


def validate(value: str | None, exclude=None) -> str:
    """The cleaned username, or ValidationError saying why it can't be used. `exclude` is the login being renamed."""
    value = clean(value)
    reason = problem(value) or (is_taken(value, exclude) and "That username is taken")
    if reason:
        raise ValidationError(reason)
    return value


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def base_from(email: str | None = None, name: str | None = None) -> str:
    """A starting point: the email before the @ (without any +tag), else the name with full stops for spaces."""
    raw = ""
    if email and "@" in email:
        raw = email.split("@", 1)[0].split("+", 1)[0]
    if len(re.sub(r"[^a-z0-9]", "", _ascii(raw))) < MIN and name:
        raw = name
    base = re.sub(r"[^a-z0-9._]+", ".", _ascii(raw))
    base = re.sub(r"\.{2,}", ".", base).strip("._")[: MAX - 4].strip("._")
    if base.isdigit():
        base = f"user.{base}"[: MAX - 4]
    return base if len(base) >= MIN else "member"


def suggest(email: str | None = None, name: str | None = None, wanted: str | None = None, n: int = 3) -> list[str]:
    """Up to `n` free usernames, closest first: what they wanted or the email/name as it is, then with numbers."""
    base = re.sub(r"\.{2,}", ".", re.sub(r"[^a-z0-9._]+", "", clean(wanted))).strip("._")[: MAX - 4].strip("._")
    if len(base) < MIN or base.isdigit():
        base = base_from(email, name)
    tries = [base, base.replace(".", "_")] + [f"{base}{i}" for i in range(2, 10)] + [f"{base}{secrets.randbelow(9000) + 1000}" for _ in range(6)]
    tries = list(dict.fromkeys(t for t in tries if not problem(t)))
    taken = set(get_user_model().objects.filter(username__in=tries).values_list("username", flat=True))
    return [t for t in tries if t not in taken][:n]


def generate(email: str | None = None, name: str | None = None) -> str:
    """A free username for someone who wasn't given one."""
    return suggest(email, name, n=1)[0]
