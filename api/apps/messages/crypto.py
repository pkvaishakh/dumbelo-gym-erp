"""Credentials kept in the database, encrypted with `FIELD_ENCRYPTION_KEY`.

The setting is a list of Fernet keys, newest first (MultiFernet): new values are written with the first, and any
of them can read. To rotate, put a new key first, run `manage.py rotate_credentials`, then drop the old key
(docs/deploy.md). Nothing here logs, and nothing here should: what passes through is a secret.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet
from django.apps import apps
from django.conf import settings
from django.db import models, transaction


@lru_cache(maxsize=4)
def _fernet(keys: tuple[str, ...]) -> MultiFernet:
    return MultiFernet([Fernet(key) for key in keys])


def fernet() -> MultiFernet:
    """The keys this server has, as one MultiFernet. Keyed on the setting, so a test that changes it gets new ones."""
    return _fernet(tuple(settings.FIELD_ENCRYPTION_KEY))


def encrypt(text: str) -> str:
    return fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    """Raises cryptography's InvalidToken when none of the keys wrote it."""
    return fernet().decrypt(token.encode()).decode()


class EncryptedTextField(models.TextField):
    """Text kept encrypted in the database and plain in Python, so only code that reads the attribute sees it.

    Every write encrypts afresh (Fernet adds a random IV), so the column can't be filtered or made unique on.
    Querysets that only show an account defer these columns, so a list never decrypts anything.
    """

    def from_db_value(self, value, expression, connection):
        return value if value in (None, "") else decrypt(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return value if value in (None, "") else encrypt(value)


def encrypted_fields(model) -> list[str]:
    return [f.name for f in model._meta.get_fields() if isinstance(f, EncryptedTextField)]


@transaction.atomic
def rotate_all() -> int:
    """Write every encrypted value again with the first key, so the older keys can be dropped. Says how many rows.

    All or nothing: a value none of the keys can read stops it, and nothing is changed.
    """
    rows = 0
    for model in apps.get_models():
        if not (fields := encrypted_fields(model)):
            continue
        # Read them all before writing any: a row no key can read stops it here, with nothing written. A few rows a
        # gym at most, so no need to stream them.
        values = [(obj.pk, {f: getattr(obj, f) for f in fields}) for obj in model.objects.only("pk", *fields)]
        for pk, plain in values:
            # update(), not save(): the values are the same, so nothing else (updated_at) should look changed
            model.objects.filter(pk=pk).update(**plain)
        rows += len(values)
    return rows
