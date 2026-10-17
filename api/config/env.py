"""What a server has to be told. `PRODUCTION=true` means nothing here may fall back to a laptop's default."""

# SECRET_KEY signs the tokens, ALLOWED_HOSTS is the names the API answers on, DATABASE_URL its Postgres, and
# CACHE_URL the Redis the rate-limit counts live in — several gunicorn workers can't each keep their own.
NEEDED_IN_PRODUCTION = ("SECRET_KEY", "ALLOWED_HOSTS", "DATABASE_URL", "CACHE_URL")


def missing_in_production(env) -> list[str]:
    """The settings from NEEDED_IN_PRODUCTION this environment hasn't been given, in the order they're listed."""
    return [name for name in NEEDED_IN_PRODUCTION if not env.str(name, default="").strip()]
