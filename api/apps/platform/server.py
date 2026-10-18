"""The Console's Server screen: whether what Rackline runs on is answering, what the jobs did, and Run Now.

Every check has a time limit and catches its own failure, so anything down shows as down, never as an error page;
with the database down, what is read from it shows as unknown. Rackline admins only (views.py). `/api/health/` stays
the load balancer's question and says no more than whether the API reaches its database.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

import redis
from celery import Task
from django.conf import settings
from django.db import DatabaseError, IntegrityError
from django.db.models import Max, OuterRef, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.billing.tasks import write_invoices
from apps.core import jobs
from apps.core.errors import RuleBroken
from apps.core.models import JobRun
from apps.core.views import database_ok
from apps.messages.models import Message, WebhookEvent, WhatsAppAccount
from apps.messages.tasks import REPLAY_DAYS, replay_webhook_calls, send_reminders
from config.celery import app as celery_app

log = logging.getLogger(__name__)

UP, DOWN, OFF, UNKNOWN = "up", "down", "off", "unknown"
STATES = [(UP, "Up"), (DOWN, "Down"), (OFF, "Not used here"), (UNKNOWN, "Can't tell")]
CHECKS = [("database", "Database"), ("redis", "Redis"), ("worker", "Worker"), ("beat", "Beat")]
PROBE_SECONDS = 2  # the longest any one check waits
BEAT_LATE = timedelta(minutes=5)  # beat ticks the retries every minute, so five quiet minutes means it stopped


@dataclass
class Job:
    """A job as the Server screen shows it: when it runs, its counts in words, and its task if Run Now can start it."""

    schedule: str
    counts: list[tuple[str, str]]
    task: Task | None = None


JOBS: dict[str, Job] = {
    JobRun.REMINDERS: Job("Every 15 minutes, at each gym's reminder hour", [
        ("listed", "reminders listed"), ("sent", "sent"), ("failed", "not sent"), ("skipped", "skipped: no number or opted out"),
        ("owner_reminders", "invoice reminders to owners"),
    ], send_reminders),
    JobRun.INVOICES: Job("Every hour, on each gym's billing day", [
        ("written", "invoices written"), ("failed", "gyms whose invoice couldn't be written"),
    ], write_invoices),
    JobRun.RETRIES: Job("Every minute", [
        ("sent", "sent"), ("waiting", "waiting again"), ("failed", "failed for good"), ("interrupted", "stopped mid-send, not retried"),
    ]),
    JobRun.WEBHOOK_REPLAY: Job(f"Only with Run Now: Meta's calls of the last {REPLAY_DAYS} days that failed", [
        ("handled", "calls handled"), ("failed", "still failing"),
    ], replay_webhook_calls),
}


@dataclass
class Check:
    key: str
    label: str
    state: str
    detail: str
    at: datetime | None = field(default=None)


def check_database() -> Check:
    if database_ok():
        return Check("database", "Database", UP, "Answering")
    return Check("database", "Database", DOWN, "Postgres isn't answering")


def _redis_urls() -> dict[str, str]:
    """The Redis servers this API uses, by what they hold: the job queue and the rate-limit counts (CACHE_URL)."""
    urls = {}
    if settings.CELERY_BROKER_URL.startswith(("redis://", "rediss://")):
        urls["job queue"] = settings.CELERY_BROKER_URL
    cache = settings.CACHES["default"]
    if "redis" in cache["BACKEND"].lower():
        location = cache["LOCATION"]
        urls["rate limits"] = location[0] if isinstance(location, (list, tuple)) else location
    return urls


def _redis_answers(url: str) -> bool:
    try:
        return bool(redis.Redis.from_url(url, socket_connect_timeout=PROBE_SECONDS, socket_timeout=PROBE_SECONDS).ping())
    except (redis.RedisError, OSError):
        return False


def check_redis() -> tuple[Check, bool]:
    """Each Redis the API uses answers a ping (once per server, when both use one), and whether the job queue's
    did. Its address is never shown: it can carry a password."""
    urls = _redis_urls()
    if not urls:
        return Check("redis", "Redis", OFF, "No Redis set"), False
    answers = {url: _redis_answers(url) for url in set(urls.values())}
    down = [what for what, url in urls.items() if not answers[url]]
    queue_up = "job queue" in urls and "job queue" not in down
    if down:
        return Check("redis", "Redis", DOWN, f"No answer: {', '.join(down)}"), queue_up
    return Check("redis", "Redis", UP, "Answering"), queue_up


def check_worker(queue_up: bool) -> Check:
    """A Celery worker answers a ping within PROBE_SECONDS. Not asked when the job queue itself is down: the
    broker's client would keep trying to connect."""
    if not settings.CELERY_BROKER_URL:
        return Check("worker", "Worker", OFF, "Jobs run in the API")
    if not queue_up and settings.CELERY_BROKER_URL.startswith(("redis://", "rediss://")):
        return Check("worker", "Worker", UNKNOWN, "Job queue is down")
    try:
        replies = celery_app.control.ping(timeout=PROBE_SECONDS, limit=1)
    except Exception:  # whatever the broker's client raises when it can't get through
        log.exception("The Server screen couldn't ping the Celery worker")
        replies = []
    if replies:
        return Check("worker", "Worker", UP, "Answering")
    return Check("worker", "Worker", DOWN, f"No answer in {PROBE_SECONDS} seconds")


def check_beat(now: datetime) -> Check:
    """Beat's last tick is the newest run it started: the retries job runs every minute, even with nothing to do."""
    if not settings.CELERY_BROKER_URL:
        return Check("beat", "Beat", OFF, "No schedule here")
    last = JobRun.objects.filter(trigger=JobRun.BEAT, started_at__isnull=False).aggregate(at=Max("started_at"))["at"]
    if last is None:
        return Check("beat", "Beat", DOWN, "No tick yet")
    if now - last > BEAT_LATE:
        return Check("beat", "Beat", DOWN, "Late", last)
    return Check("beat", "Beat", UP, "Ticking", last)


def job_rows() -> list[dict]:
    """Each job with its run under way (if any) and its last finished run: five queries whatever the history."""
    current = {r.job: r for r in JobRun.objects.filter(finished_at__isnull=True).select_related("by").order_by("-created_at")}
    rows = []
    for job, spec in JOBS.items():
        last = JobRun.objects.filter(job=job, finished_at__isnull=False).select_related("by").first()
        rows.append({"job": job, "label": dict(JobRun.JOBS)[job], "schedule": spec.schedule, "can_run": spec.task is not None,
                     "current": current.get(job), "last_run": last})
    return rows


def message_counts(now: datetime) -> dict[str, int]:
    """Messages waiting for a retry, and those that failed today (Rackline's day, India time)."""
    start = datetime.combine(timezone.localdate(now), time.min, tzinfo=timezone.get_current_timezone())
    return {
        "waiting_retry": Message.objects.filter(status=Message.QUEUED, next_retry_at__isnull=False).count(),
        "failed_today": Message.objects.filter(status=Message.FAILED, updated_at__gte=start).count(),
    }


def webhook_status(now: datetime) -> dict:
    """Meta's calls that couldn't be handled lately, and when Meta last called each number."""
    latest = WebhookEvent.objects.filter(account=OuterRef("pk")).order_by("-created_at").values("created_at")[:1]
    numbers = (WhatsAppAccount.objects.annotate(last_call_at=Subquery(latest))
               .values("id", "display_number", "gym_id", "gym__name", "last_call_at"))
    return {
        "failed_days": REPLAY_DAYS,
        "failed": WebhookEvent.objects.filter(created_at__gte=now - timedelta(days=REPLAY_DAYS)).exclude(error="").count(),
        "numbers": [{"id": n["id"], "display_number": n["display_number"], "gym_name": n["gym__name"], "is_shared": n["gym_id"] is None,
                     "last_call_at": n["last_call_at"]} for n in numbers],
    }


def _deployed_at() -> datetime | None:
    try:
        return parse_datetime(settings.DEPLOYED_AT) if settings.DEPLOYED_AT else None
    except ValueError:  # well formed but impossible, such as month 13
        return None


def status(now: datetime | None = None) -> dict:
    """Everything the Server screen shows. What comes from the database is None when it can't be read."""
    now = now or timezone.now()
    db = check_database()

    def read(what, fn):
        if db.state != UP:
            return None
        try:
            return fn()
        except DatabaseError:
            log.exception("The Server screen couldn't read %s", what)
            return None

    queue, queue_up = check_redis()
    beat = read("beat's last tick", lambda: check_beat(now)) or Check("beat", "Beat", UNKNOWN, "Database is down")
    return {
        "version": settings.APP_VERSION,
        "deployed_at": _deployed_at(),
        "checked_at": now,
        "checks": [db, queue, check_worker(queue_up), beat],
        "jobs": read("the jobs", job_rows),
        "messages": read("the messages", lambda: message_counts(now)),
        "webhook": read("the webhook", lambda: webhook_status(now)),
    }


def run_now(job: str, by) -> JobRun:
    """Queue one run of a safe-to-repeat job on the worker, refused while that job is queued or running. In a
    process with no worker (a laptop) it runs here, and its run keeps any error."""
    task = JOBS[job].task
    label = dict(JobRun.JOBS)[job]
    busy = RuleBroken("job_running", f"{label} is running now. Wait for it to finish, then try again.")
    jobs.close_abandoned(job, timezone.now())
    if jobs.running(job):
        raise busy
    try:
        run = jobs.queue(job, by)
    except IntegrityError:  # another press got there first
        raise busy from None
    try:
        task.apply_async(kwargs={"run_id": run.pk})
    except Exception:
        run.refresh_from_db()
        if run.started_at is not None:
            log.exception("Run Now's %s run %s broke", job, run.pk)  # ran here, with no worker: its run says why
        else:
            log.exception("Run Now couldn't queue %s", job)
            JobRun.objects.filter(pk=run.pk).update(finished_at=timezone.now(), error="The job queue didn't take it")
            raise RuleBroken("queue_down", "The job couldn't be queued: the job queue isn't answering. Check Redis above, then try again.",
                             status=503) from None
    run.refresh_from_db()
    return run
