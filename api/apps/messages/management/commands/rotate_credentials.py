"""Encrypt every stored credential again with the first FIELD_ENCRYPTION_KEY: `python manage.py rotate_credentials`.

Run it after putting a new key first in FIELD_ENCRYPTION_KEY (keeping the old one after it), then drop the old key.
Safe to run again. See docs/deploy.md.
"""
from cryptography.fernet import InvalidToken
from django.core.management.base import BaseCommand, CommandError

from apps.messages.crypto import rotate_all


class Command(BaseCommand):
    help = "Write every encrypted credential again with the newest FIELD_ENCRYPTION_KEY, so older keys can be dropped."

    def handle(self, *args, **kw):
        try:
            rows = rotate_all()
        except InvalidToken:
            raise CommandError("A stored credential can't be read with any key in FIELD_ENCRYPTION_KEY. Put the old key "
                               "back (after the new one) and run this again. Nothing was changed.")
        self.stdout.write(f"{rows} row{'s' if rows != 1 else ''} encrypted with the newest key.")
