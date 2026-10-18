"""Rackline API settings. Everything that differs between machines comes from the environment (see .env.example)."""
from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

from config.env import DEV_ENCRYPTION_KEY, bad_encryption_keys, missing_in_production

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    PRODUCTION=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
)
environ.Env.read_env(BASE_DIR / ".env")

# PRODUCTION=true on every deployed server: no default secret, no debug, HTTPS only (see the end of this file).
PRODUCTION = env("PRODUCTION")
if PRODUCTION and (missing := missing_in_production(env)):
    raise ImproperlyConfigured(f"PRODUCTION=true needs {', '.join(missing)} in the environment (see docs/deploy.md)")
SECRET_KEY = env("SECRET_KEY") if PRODUCTION else env("SECRET_KEY", default="dev-only-not-a-secret-change-me-in-production-0000")
DEBUG = env("DEBUG")
if PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DEBUG must be off when PRODUCTION is on")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.gyms",
    "apps.members",
    "apps.attendance",
    "apps.tasks",
    "apps.expenses",
    "apps.payroll",
    "apps.finance",
    "apps.audit",
    "apps.reports",
    "apps.reminders",
    "apps.messages",
    "apps.platform",
    "apps.billing",
]

MIDDLEWARE = [
    # Before anything that reads the Host header: the load balancer checks the container at its own address.
    "apps.core.middleware.HealthCheckHost",
    "django.middleware.security.SecurityMiddleware",
    # Serves /static/ (the admin and the docs page) straight from gunicorn, so a deploy needs no bucket or CDN.
    # runserver serves static files itself, so on a laptop this middleware never has anything to do.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

# PostgreSQL in every real environment; SQLite only as a zero-setup fallback for a quick look.
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Throttle counts live here. Local memory is fine for one process; set CACHE_URL=redis://... when there are several.
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailOrPhoneBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"  # a gym's own time zone is stored on the gym; this is only the default
USE_I18N = True
USE_TZ = True  # stored in UTC, shown in the gym's time zone

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # `collectstatic` writes a compressed copy of every file next to it, which is what whitenoise serves.
    # Names are not hashed: the only static files Rackline has are the admin's and the docs page's.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.params.Pages",
    "PAGE_SIZE": 50,
    # Only views that name a throttle_scope (or their own throttles) are limited: sign-in, refresh, QR, turnstile.
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "login": env("THROTTLE_LOGIN", default="10/min"),  # per account
        "login_ip": env("THROTTLE_LOGIN_IP", default="60/min"),  # per address
        "refresh": env("THROTTLE_REFRESH", default="30/min"),
        "qr": env("THROTTLE_QR", default="20/min"),
        "device": env("THROTTLE_DEVICE", default="600/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.errors.exception_handler",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,  # a used or signed-out refresh token stops working
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Rackline API",
    "DESCRIPTION": "Gym management for many gyms. Send `X-Gym: <gym slug>` with every call inside a gym.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",  # set, not detected: detection uses os.path and breaks on Windows (tags become "api")
    # Several models have a `kind` or `status`; name the payroll and dues ones so the web's types read clearly.
    "ENUM_NAME_OVERRIDES": {
        "MessageStatusEnum": "apps.messages.models.Message.STATUSES",
        "StateEnum": "apps.expenses.serializers.ExpenseDueSerializer.STATES",  # its name before other states came
        "ServerCheckEnum": "apps.platform.server.CHECKS",
        "ServerStateEnum": "apps.platform.server.STATES",
        "JobRunStateEnum": "apps.platform.serializers.JobRunSerializer.STATES",
        "JobTriggerEnum": "apps.core.models.JobRun.TRIGGERS",
        "SalaryItemKindEnum": "apps.payroll.models.SalaryItem.KINDS",
        "PayslipLineKindEnum": "apps.payroll.models.PayslipLine.KINDS",
        "PayslipStatusEnum": "apps.payroll.models.Payslip.STATUSES",
        "ExpenseDueStatusEnum": "apps.expenses.models.ExpenseDue.STATUSES",
        "AccountKindEnum": "apps.finance.models.Account.KINDS",
        "MoneyMoveKindEnum": "apps.finance.models.MoneyMove.KINDS",
        "StatementEntryKindEnum": "apps.finance.models.StatementTick.KINDS",
        "TaskStatusEnum": "apps.tasks.models.Task.STATUSES",
        "GymStatusEnum": "apps.gyms.models.Gym.STATUS",
        "BranchAskStatusEnum": "apps.billing.models.BranchRequest.STATUS",
        "WhatsappModeEnum": "apps.billing.models.GymBilling.WHATSAPP_MODES",
        "InvoiceStatusEnum": "apps.billing.models.Invoice.STATUS",
        "InvoiceLineKindEnum": "apps.billing.models.InvoiceLine.KINDS",
        "RacklinePayMethodEnum": "apps.billing.models.InvoicePayment.METHODS",
        "WhatsappAccountStatusEnum": "apps.messages.models.WhatsAppAccount.STATUS",
        "WhatsappTemplateStatusEnum": "apps.messages.models.WhatsAppTemplate.STATUS",
        "WhatsappCategoryEnum": "apps.messages.models.WhatsAppTemplate.CATEGORIES",
        "CategoryEnum": "apps.expenses.models.Expense.CATEGORIES",  # named, now that templates have categories too
        "MessageKindEnum": "apps.messages.models.WhatsAppTemplate.KINDS",
        "GymWhatsappStatusEnum": "apps.messages.serializers.GymWhatsAppSerializer.STATES",
        "MethodEnum": "apps.members.models.Payment.METHODS",  # named, now that Rackline payments have methods of their own
    },
}
# ---- What is running (the Console's Server screen) ----
# The deploy sets both: the release (a git tag or commit) and when it went out (ISO 8601, e.g. 2026-10-18T09:30:00Z).
APP_VERSION = env("APP_VERSION", default="") or "dev"
DEPLOYED_AT = env("DEPLOYED_AT", default="")

# ---- Background jobs (see config/celery.py) ----
# No broker means no worker: tasks run where they are called, which is what the tests and a laptop without
# Redis want. A server sets CELERY_BROKER_URL to its Redis.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="")
CELERY_TASK_ALWAYS_EAGER = not CELERY_BROKER_URL
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TIMEZONE = "UTC"  # beat ticks in UTC; each gym's own clock decides when its day starts (apps/core/clock.py)
CELERY_BEAT_SCHEDULE = {
    "reminders": {
        # Writes the day's reminder list and sends it, at the hours Rackline set (apps/messages/automation.py, read
        # each tick), and reminds owners about Rackline invoices; apps.reminders.tasks.sweep_reminders writes a
        # list on its own, for a morning that has to be rebuilt by hand.
        "task": "apps.messages.tasks.send_reminders",
        # Every quarter hour, not every hour: India is UTC+5:30 and Nepal +5:45, so a tick on the hour would
        # reach them at 6:30 and 6:45 their own time. The sweep is safe to repeat, so the extra ticks cost nothing.
        "schedule": crontab(minute="*/15"),
    },
    "rackline-invoices": {
        # Each gym's Rackline invoice on its billing day, from Rackline's invoice hour on the gym's clock (read from the
        # database each tick, so changing it needs no restart). Hourly: the job skips a month already written, so
        # the later ticks that day do nothing.
        "task": "apps.billing.tasks.write_invoices",
        "schedule": crontab(minute=5),
    },
    "message-retries": {
        # Messages Meta turned away for now (rate limits, Meta busy), tried again once their wait is over
        "task": "apps.messages.tasks.retry_messages",
        "schedule": crontab(),  # every minute: the shortest wait is a minute
    },
}

# ---- Credentials kept in the database (see apps/messages/crypto.py) ----
# Comma-separated Fernet keys, newest first: values are written with the first and read with any of them, so a
# key is rotated by putting a new one first (docs/deploy.md). A laptop gets a fixed dev-only key.
FIELD_ENCRYPTION_KEY = env.list("FIELD_ENCRYPTION_KEY", default=[]) or ([] if PRODUCTION else [DEV_ENCRYPTION_KEY])
if bad := bad_encryption_keys(FIELD_ENCRYPTION_KEY):
    raise ImproperlyConfigured(
        f"FIELD_ENCRYPTION_KEY: key {', '.join(map(str, bad))} isn't a Fernet key. Make one with "
        "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"` (docs/deploy.md)"
    )

# ---- WhatsApp (see apps/messages/senders.py) ----
# `fake` sends nothing and keeps what it would have sent, so a laptop and the tests need no WhatsApp account.
# A server that really sends sets WHATSAPP_PROVIDER=whatsapp_cloud, which posts templates to Meta's Cloud API. The numbers and their keys are WhatsApp
# accounts in the database (the Console's WhatsApp screen), not settings: Rackline's shared number is one of them.
WHATSAPP_PROVIDER = env("WHATSAPP_PROVIDER", default="fake")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="v23.0")  # Meta's Graph API version, in every call's path

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_HEADERS = ["authorization", "content-type", "x-gym", "x-device-token"]

if PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # behind the load balancer
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]  # the load balancer checks over plain HTTP; a redirect isn't healthy
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True  # api.<domain> is HTTPS from its first day, so it can be on the preload list
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
