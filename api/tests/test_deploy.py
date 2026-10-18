"""What a deploy depends on: the health check, and settings a server must be given (see docs/deploy.md)."""
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import environ
from django.db import DatabaseError
from rest_framework.test import APIClient

from apps.core import views
from config.env import NEEDED_IN_PRODUCTION, missing_in_production

API_DIR = Path(__file__).resolve().parent.parent
PRODUCTION_ENV = {
    "PRODUCTION": "true",
    "DEBUG": "False",
    "SECRET_KEY": "a-very-long-random-production-secret-key-0123456789abcdefghij",
    "ALLOWED_HOSTS": "api.rackline.in",
    "DATABASE_URL": "postgres://rackline:secret@db.ap-south-1.rds.amazonaws.com:5432/rackline",
    "CACHE_URL": "redis://cache.ap-south-1.cache.amazonaws.com:6379/1",
    "FIELD_ENCRYPTION_KEY": "cHJvZHVjdGlvbi10ZXN0LWtleS0wMDAwMDAwMDAwMDA=",
}


def fake_env(**values):
    """An Env that reads only what the test hands it, whatever the machine's own environment holds."""
    env = environ.Env()
    env.ENVIRON = values
    return env


def manage(*args, **environment):
    """`manage.py ...` in its own process, so settings are read from the environment the test describes."""
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=API_DIR,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
    )


# ---- /api/health/ ----

def test_health_needs_no_sign_in_and_no_gym(db):
    r = APIClient().get("/api/health/")

    assert r.status_code == 200, r.content
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_says_503_when_the_database_is_unreachable(db):
    with mock.patch.object(views.connection, "cursor", side_effect=DatabaseError("could not connect to server")):
        r = APIClient().get("/api/health/")

    assert r.status_code == 503
    assert r.json() == {"status": "error", "database": "unreachable"}
    assert "connect" not in r.content.decode()  # the reason goes to the log, never to whoever is asking


def test_health_answers_the_load_balancer_asking_by_ip(db, settings):
    settings.ALLOWED_HOSTS = ["api.rackline.in"]

    assert APIClient().get("/api/health/", headers={"host": "10.0.3.47"}).status_code == 200
    # Only that one path: everything else still answers only on the names the server was given.
    assert APIClient().get("/api/me/", headers={"host": "10.0.3.47"}).status_code == 400


# ---- Settings a server must be given ----

def test_production_lists_every_setting_it_was_not_given():
    assert missing_in_production(fake_env(SECRET_KEY="x", CACHE_URL=" ")) == ["ALLOWED_HOSTS", "DATABASE_URL", "CACHE_URL", "FIELD_ENCRYPTION_KEY"]
    assert missing_in_production(fake_env(**PRODUCTION_ENV)) == []


def test_production_refuses_to_start_without_them():
    for name in NEEDED_IN_PRODUCTION:
        short = {k: v for k, v in PRODUCTION_ENV.items() if k != name} | {name: ""}
        r = manage("check", **short)

        assert r.returncode != 0, r.stdout
        assert name in r.stderr and "docs/deploy.md" in r.stderr


def test_a_bad_encryption_key_refuses_to_start_without_saying_it():
    r = manage("check", **PRODUCTION_ENV | {"FIELD_ENCRYPTION_KEY": f"{PRODUCTION_ENV['FIELD_ENCRYPTION_KEY']},not-a-real-key-123"})

    assert r.returncode != 0, r.stdout
    assert "key 2 isn't a Fernet key" in r.stderr and "not-a-real-key-123" not in r.stderr


def test_check_deploy_is_clean_with_production_settings():
    r = manage("check", "--deploy", **PRODUCTION_ENV)

    assert r.returncode == 0, r.stderr
    assert "System check identified no issues" in r.stdout, r.stdout + r.stderr
