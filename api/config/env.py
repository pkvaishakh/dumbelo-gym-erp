"""What a server has to be told. `PRODUCTION=true` means nothing here may fall back to a laptop's default."""
from cryptography.fernet import Fernet

# SECRET_KEY signs the tokens, ALLOWED_HOSTS is the names the API answers on, DATABASE_URL its Postgres,
# CACHE_URL the Redis the rate-limit counts live in — several gunicorn workers can't each keep their own — and
# FIELD_ENCRYPTION_KEY the key the WhatsApp credentials are encrypted with in the database.
NEEDED_IN_PRODUCTION = ("SECRET_KEY", "ALLOWED_HOSTS", "DATABASE_URL", "CACHE_URL", "FIELD_ENCRYPTION_KEY")

# Only for a laptop and the tests: a server that used it would be encrypting with a key anyone can read here.
DEV_ENCRYPTION_KEY = "ZGV2LW9ubHktbm90LWEtc2VjcmV0LWtleS0wMDAwMDA="


def missing_in_production(env) -> list[str]:
    """The settings from NEEDED_IN_PRODUCTION this environment hasn't been given, in the order they're listed."""
    return [name for name in NEEDED_IN_PRODUCTION if not env.str(name, default="").strip()]


def bad_encryption_keys(keys: list[str]) -> list[int]:
    """Which of FIELD_ENCRYPTION_KEY's keys (1 = the first) aren't Fernet keys. Says where, never what they are."""
    bad = []
    for i, key in enumerate(keys, start=1):
        try:
            Fernet(key)
        except (ValueError, TypeError):
            bad.append(i)
    return bad
