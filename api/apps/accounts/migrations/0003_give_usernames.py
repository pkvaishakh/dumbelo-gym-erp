"""Existing logins get a username made from their email (before the @) or their name.

The rules are copied here, not imported from apps.accounts.usernames, so this migration keeps doing what it did
when those rules change."""
import re
import unicodedata

from django.db import migrations

RESERVED = {
    "admin", "administrator", "root", "system", "staff", "support", "help", "dumbelo", "console", "api", "app", "www",
    "login", "logout", "signin", "signup", "me", "settings", "null", "undefined", "owner", "gym", "member", "trainer",
    "receptionist", "desk",
}


def _base(email, name):
    def ascii_(text):
        return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()

    raw = (email or "").split("@", 1)[0].split("+", 1)[0] if email and "@" in email else ""
    if len(re.sub(r"[^a-z0-9]", "", ascii_(raw))) < 3 and name:
        raw = name
    base = re.sub(r"[^a-z0-9._]+", ".", ascii_(raw))
    base = re.sub(r"\.{2,}", ".", base).strip("._")[:26].strip("._")
    if base.isdigit():
        base = f"user.{base}"[:26]
    return base if len(base) >= 3 else "member"


def give_usernames(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    used = set()
    for user in User.objects.order_by("id"):
        base = _base(user.email, user.name)
        if base in RESERVED:
            base = f"{base}.admin" if user.is_staff else f"{base}.{user.id}"
        name, n = base, 2
        while name in used:
            name, n = f"{base}{n}", n + 1
        used.add(name)
        user.username = name
        user.save(update_fields=["username"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_username"),
    ]

    operations = [
        migrations.RunPython(give_usernames, migrations.RunPython.noop),
    ]
