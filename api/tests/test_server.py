"""Console → Server: the status of everything Dumbelo runs on, each job's runs, and Run Now."""
from datetime import timedelta
from unittest import mock

import pytest
from django.core.management import call_command
from django.db import DatabaseError, OperationalError
from django.utils import timezone
from kombu.exceptions import OperationalError as QueueDown
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.billing.tasks import write_invoices
from apps.core import views as core_views
from apps.core.jobs import ABANDONED, run_job
from apps.core.models import JobRun
from apps.messages.models import Message, WebhookEvent, WhatsAppAccount
from apps.messages.tasks import replay_webhook_calls, retry_messages, send_reminders
from apps.platform import server
from tests.test_platform import dumbelo, support

STATUS = "/api/platform/status/"


def run_now(job):
    return f"/api/platform/jobs/{job}/run/"


def message(w, status, n, **extra):
    """A message to the gym's member, in the given state."""
    return Message.objects.create(gym=w.gym, member=w.member, kind="plan_ending", dedupe_key=f"test:{status}:{n}", to=w.member.phone,
                                  text="Hi Asha", for_date=w.today, provider="fake", status=status, **extra)


def checks(body):
    return {c["key"]: c for c in body["checks"]}


@pytest.fixture
def on_a_server(settings):
    """A broker set, as on a server, with Redis and the worker answering unless a test says otherwise."""
    settings.CELERY_BROKER_URL = "redis://redis.internal:6379/0"
    with mock.patch.object(server, "_redis_answers", return_value=True), \
         mock.patch.object(server.celery_app.control, "ping", return_value=[{"celery@worker-1": {"ok": "pong"}}]) as ping:
        yield ping


# ---- who may look ----

def test_only_dumbelo_admins_see_the_status_and_run_jobs(w):
    for c in (support(), w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(STATUS).status_code == 403
        assert c.post(run_now("reminders")).status_code == 403
    assert APIClient().get(STATUS).status_code == 401
    assert not JobRun.objects.exists() and not AuditLog.objects.filter(action="job.run_now").exists()


def test_health_says_no_more_than_before(db):
    assert APIClient().get("/api/health/").json() == {"status": "ok", "database": "ok"}


# ---- the status ----

def test_the_status_shows_the_version_the_jobs_messages_and_webhook_within_a_query_budget(w, other, settings, shared_number,
                                                                                          django_assert_max_num_queries):
    settings.APP_VERSION, settings.DEPLOYED_AT = "a1b2c3d", "2026-10-18T09:30:00Z"
    now = timezone.now()
    send_reminders.apply()  # beat's tick: nothing due
    write_invoices.apply(kwargs={"day": "2026-11-01"})  # by hand: writes both gyms' invoices
    for n in range(3):
        message(w, Message.QUEUED, n, next_retry_at=now + timedelta(minutes=5))
    message(w, Message.QUEUED, 9)  # sending, not waiting for a retry
    message(other, Message.FAILED, 1)
    old = message(w, Message.FAILED, 2)
    Message.objects.filter(pk=old.pk).update(updated_at=now - timedelta(days=2))
    own = WhatsAppAccount(gym=w.gym, waba_id="100000000000002", phone_number_id="200000000000002", display_number="+91 80000 00002")
    own.set_credentials(access_token="EAAGown-number-token-1111111111", app_secret="own-number-app-secret-11")
    own.save()
    for n in range(4):
        WebhookEvent.objects.create(account=shared_number, body="{}", error="KeyError: 'entry'" if n % 2 else "")
    stale = WebhookEvent.objects.create(account=shared_number, body="{}", error="KeyError: 'entry'")
    WebhookEvent.objects.filter(pk=stale.pk).update(created_at=now - timedelta(days=8))

    with django_assert_max_num_queries(12):
        r = dumbelo().get(STATUS)

    assert r.status_code == 200, r.content
    body = r.json()
    assert body["version"] == "a1b2c3d" and body["deployed_at"] == "2026-10-18T15:00:00+05:30"
    c = checks(body)
    assert c["database"]["state"] == "up"
    assert [c[k]["state"] for k in ("redis", "worker", "beat")] == ["off", "off", "off"]  # no broker in the tests
    jobs = {j["job"]: j for j in body["jobs"]}
    assert list(jobs) == ["reminders", "invoices", "retries", "webhook_replay"]
    assert [jobs[j]["can_run"] for j in jobs] == [True, True, False, True]
    reminders, invoices = jobs["reminders"]["last_run"], jobs["invoices"]["last_run"]
    assert reminders["trigger"] == "beat" and reminders["state"] == "done" and reminders["did"] == [] and reminders["seconds"] >= 0
    assert invoices["trigger"] == "by_hand" and invoices["did"] == [{"label": "invoices written", "count": 2}]
    assert jobs["retries"]["last_run"] is None and jobs["retries"]["current"] is None
    assert body["messages"] == {"waiting_retry": 3, "failed_today": 1}
    assert body["webhook"]["failed"] == 2 and body["webhook"]["failed_days"] == 7
    numbers = {n["display_number"]: n for n in body["webhook"]["numbers"]}
    assert numbers["+91 80000 00009"]["is_shared"] and numbers["+91 80000 00009"]["last_call_at"]
    assert numbers["+91 80000 00002"] == {"id": own.pk, "display_number": "+91 80000 00002", "gym_name": w.gym.name,
                                          "is_shared": False, "last_call_at": None}
    assert "token" not in r.content.decode() and "secret" not in r.content.decode()


def test_a_dead_database_shows_as_down_not_a_500(w):
    ops = dumbelo()
    with mock.patch.object(core_views.connection, "cursor", side_effect=DatabaseError("could not connect to server")):
        r = ops.get(STATUS)

    assert r.status_code == 200, r.content
    body = r.json()
    assert checks(body)["database"]["state"] == "down"
    assert checks(body)["beat"]["state"] == "unknown"
    assert body["jobs"] is None and body["messages"] is None and body["webhook"] is None
    assert "connect" not in r.content.decode()


def test_a_section_the_database_breaks_on_is_left_out_not_a_500(w):
    with mock.patch.object(server, "job_rows", side_effect=OperationalError("server closed the connection")):
        r = dumbelo().get(STATUS)

    assert r.status_code == 200 and r.json()["jobs"] is None and r.json()["messages"] is not None


def test_dead_redis_shows_as_down_and_the_worker_is_not_asked(w, settings):
    settings.CELERY_BROKER_URL = "redis://redis.internal:6379/0"
    with mock.patch.object(server, "_redis_answers", return_value=False), mock.patch.object(server.celery_app.control, "ping") as ping:
        c = checks(dumbelo().get(STATUS).json())

    assert c["redis"]["state"] == "down" and c["redis"]["detail"] == "No answer: job queue"
    assert "redis.internal" not in str(c)  # an address can carry a password
    assert c["worker"]["state"] == "unknown"
    ping.assert_not_called()


def test_redis_pings_have_a_time_limit_and_a_refused_connection_is_down(settings):
    with mock.patch.object(server.redis.Redis, "from_url", wraps=server.redis.Redis.from_url) as made:
        assert server._redis_answers("redis://127.0.0.1:1/0") is False  # nothing listens on port 1
    assert made.call_args.kwargs == {"socket_connect_timeout": 2, "socket_timeout": 2}


def test_a_dead_worker_shows_as_down(w, on_a_server):
    ops = dumbelo()
    on_a_server.return_value = []
    c = checks(ops.get(STATUS).json())
    assert c["redis"]["state"] == "up" and c["worker"]["state"] == "down"
    assert c["worker"]["detail"] == "No answer in 2 seconds"
    assert on_a_server.call_args.kwargs == {"timeout": 2, "limit": 1}

    on_a_server.side_effect = QueueDown("Error 111 connecting")
    assert checks(ops.get(STATUS).json())["worker"]["state"] == "down"


def test_beat_is_up_while_it_ticks_and_down_when_it_stops(w, on_a_server):
    ops = dumbelo()
    assert checks(ops.get(STATUS).json())["beat"]["state"] == "down"  # never ticked

    retry_messages.apply()  # beat's every-minute tick
    beat = checks(ops.get(STATUS).json())["beat"]
    assert beat["state"] == "up" and beat["at"]
    assert checks(ops.get(STATUS).json())["worker"]["state"] == "up"

    JobRun.objects.update(started_at=timezone.now() - timedelta(minutes=6))
    assert checks(ops.get(STATUS).json())["beat"]["state"] == "down"
    write_invoices.apply(kwargs={"day": "2026-11-01"})  # a run by hand isn't beat ticking
    assert checks(ops.get(STATUS).json())["beat"]["state"] == "down"


# ---- Run Now ----

def test_run_now_queues_once_is_refused_while_the_job_runs_and_is_audited(w):
    ops = dumbelo()
    with mock.patch.object(send_reminders, "apply_async") as queued:
        r = ops.post(run_now("reminders"))
        again = ops.post(run_now("reminders"))

    assert r.status_code == 202, r.content
    run = r.json()
    assert run["state"] == "queued" and run["trigger"] == "run_now" and run["by_name"] == "Dumbelo Ops"
    queued.assert_called_once_with(kwargs={"run_id": run["id"]})
    assert again.status_code == 409 and again.json()["error"]["code"] == "job_running"
    assert again.json()["error"]["message"] == "Reminders is running now. Wait for it to finish, then try again."
    log = AuditLog.objects.get(action="job.run_now")
    assert log.gym is None and log.actor.email == "ops@dumbelo.com" and log.after == {"job": "reminders"}
    assert dumbelo("ops2@dumbelo.com").get(STATUS).json()["jobs"][0]["current"]["id"] == run["id"]

    send_reminders.apply(kwargs={"run_id": run["id"]})  # the worker takes it
    send_reminders.apply(kwargs={"run_id": run["id"]})  # and the queue hands it over again: nothing more
    done = JobRun.objects.get(pk=run["id"])
    assert done.finished_at and done.trigger == JobRun.RUN_NOW and JobRun.objects.filter(job="reminders").count() == 1
    with mock.patch.object(send_reminders, "apply_async"):
        assert ops.post(run_now("reminders")).status_code == 202  # finished, so it can run again
    assert AuditLog.objects.filter(action="job.run_now").count() == 2


def test_run_now_is_refused_while_beat_is_running_that_job(w):
    JobRun.objects.create(job=JobRun.INVOICES, trigger=JobRun.BEAT, started_at=timezone.now())
    with mock.patch.object(write_invoices, "apply_async") as queued:
        r = dumbelo().post(run_now("invoices"))
    assert r.status_code == 409 and r.json()["error"]["code"] == "job_running"
    queued.assert_not_called()
    assert not AuditLog.objects.filter(action="job.run_now").exists()


def test_a_run_left_unfinished_for_an_hour_no_longer_blocks_run_now(w):
    stuck = JobRun.objects.create(job=JobRun.WEBHOOK_REPLAY, trigger=JobRun.RUN_NOW)
    JobRun.objects.filter(pk=stuck.pk).update(created_at=timezone.now() - timedelta(hours=2))
    with mock.patch.object(replay_webhook_calls, "apply_async"):
        assert dumbelo().post(run_now("webhook_replay")).status_code == 202
    stuck.refresh_from_db()
    assert stuck.finished_at and stuck.error == ABANDONED


def test_run_now_only_starts_the_safe_to_repeat_jobs(w):
    ops = dumbelo()
    assert ops.post(run_now("retries")).status_code == 404
    assert ops.post(run_now("backups")).status_code == 404
    assert not JobRun.objects.exists()


def test_run_now_without_a_worker_runs_here(w, shared_number):
    """A laptop: no broker, so the job runs in the request and the run is finished when it answers."""
    event = WebhookEvent.objects.create(account=shared_number, body='{"entry": []}', error="KeyError: 'entry'")
    r = dumbelo().post(run_now("webhook_replay"))
    assert r.status_code == 202 and r.json()["state"] == "done"
    assert r.json()["did"] == [{"label": "calls handled", "count": 1}]
    event.refresh_from_db()
    assert event.error == ""


def test_run_now_says_so_when_the_queue_is_down_and_does_not_block_the_next_try(w):
    ops = dumbelo()
    with mock.patch.object(send_reminders, "apply_async", side_effect=QueueDown("Error 111 connecting")):
        r = ops.post(run_now("reminders"))
    assert r.status_code == 503 and r.json()["error"]["code"] == "queue_down"
    assert JobRun.objects.get().error == "The job queue didn't take it"
    with mock.patch.object(send_reminders, "apply_async"):
        assert ops.post(run_now("reminders")).status_code == 202


# ---- every job keeps its runs ----

def test_every_job_writes_its_run(w, shared_number):
    send_reminders.apply()
    write_invoices.apply()
    retry_messages.apply()
    replay_webhook_calls.apply()
    assert sorted(JobRun.objects.filter(trigger=JobRun.BEAT).values_list("job", flat=True)) == ["invoices", "reminders", "retries", "webhook_replay"]
    assert not JobRun.objects.filter(finished_at__isnull=True).exists()

    send_reminders.apply(kwargs={"at": "2026-06-01T00:30:00+00:00"})
    call_command("write_invoices", "--day", "2026-11-01")
    call_command("replay_webhook_events", "--since", "2026-01-01")
    by_hand = JobRun.objects.filter(trigger=JobRun.BY_HAND)
    assert sorted(by_hand.values_list("job", flat=True)) == ["invoices", "reminders", "webhook_replay"]
    assert by_hand.get(job="invoices").counts == {"written": 1, "failed": 0}


def test_a_job_that_breaks_keeps_the_error_and_still_raises(w):
    with mock.patch("apps.messages.tasks.reminder_tick", side_effect=OperationalError("deadlock detected\nDETAIL: Process 12 waits")):
        with pytest.raises(OperationalError):
            send_reminders.apply().get()
    run = JobRun.objects.get()
    assert run.finished_at and run.error == "OperationalError: deadlock detected" and not run.idle


def test_idle_runs_are_kept_only_as_the_latest_and_the_rest_for_30_days(w):
    def tick(counts):
        run_job(JobRun.RETRIES, lambda: counts)
        return list(JobRun.objects.filter(job=JobRun.RETRIES).order_by("id").values_list("counts", flat=True))

    assert tick({"sent": 0}) == [{"sent": 0}]
    assert tick({"sent": 0}) == [{"sent": 0}]  # the earlier idle tick goes
    assert tick({"sent": 2}) == [{"sent": 2}]
    assert tick({"sent": 0}) == [{"sent": 2}, {"sent": 0}]  # what did something stays
    JobRun.objects.filter(counts={"sent": 2}).update(created_at=timezone.now() - timedelta(days=31))
    assert tick({"sent": 1}) == [{"sent": 1}]  # past 30 days it goes too
    run_job(JobRun.INVOICES, lambda: {"written": 0})
    assert JobRun.objects.filter(job=JobRun.RETRIES).count() == 1  # each job prunes its own
