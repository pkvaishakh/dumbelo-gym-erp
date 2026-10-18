"""Sending through Meta: the template Meta gets, the number it goes from, and never sending one twice."""
import io
import json
from datetime import timedelta
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest
from django.utils import timezone

from apps.billing.models import GymBilling
from apps.billing.services import change_plan
from apps.core import clock
from apps.gyms.models import Gym
from apps.members.models import Member
from apps.messages import accounts, services
from apps.messages.meta import template_payload
from apps.messages.models import Message, WhatsAppTemplate
from apps.messages.senders import FakeSender
from apps.messages.services import send_due, send_retries
from apps.messages.tasks import retry_messages, send_reminders
from apps.platform.services import suspend
from apps.reminders.models import ReminderDue
from apps.reminders.services import queue_for

SHARED_TOKEN = "EAAGshared-test-token-0000000000"  # conftest's shared number
OWN = {"waba_id": "100000000000002", "phone_number_id": "200000000000002", "display_number": "+91 80000 00002",
       "access_token": "EAAGown-number-token-1111111111", "app_secret": "own-number-app-secret-11"}


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Graph:
    """Stands in for Meta's Graph API. Answers each call with the next of `answers` (the last one repeats): a dict
    is a 200 with that body, an exception is raised. Remembers every request and its JSON body."""

    def __init__(self, *answers):
        self.answers, self.requests = list(answers) or [accepted()], []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        answer = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        if isinstance(answer, HTTPError):
            answer.fp.seek(0)  # the same refusal again, body and all
        if isinstance(answer, BaseException):
            raise answer
        return Answer(json.dumps(answer).encode())

    @property
    def bodies(self):
        return [json.loads(r.data) for r in self.requests]


def accepted(n=1):
    return {"messaging_product": "whatsapp", "contacts": [{"input": "919811111117", "wa_id": "919811111117"}],
            "messages": [{"id": f"wamid.HBgM{n:04d}", "message_status": "accepted"}]}


def refused(code, message="Error", status=400):
    body = {"error": {"message": message, "type": "OAuthException", "code": code, "fbtrace_id": "Abc"}}
    return HTTPError("https://graph.facebook.com/x", status, "Error", hdrs=None, fp=io.BytesIO(json.dumps(body).encode()))


@pytest.fixture
def cloud(settings):
    """The real sender, talking to a stand-in Meta."""
    settings.WHATSAPP_PROVIDER, settings.WHATSAPP_API_VERSION = "whatsapp_cloud", "v23.0"


def fresh(gym) -> Gym:
    """The gym as the morning job loads it: its Rackline plan read anew."""
    return Gym.objects.get(pk=gym.pk)


def remind(w, graph, day=None):
    day = day or w.today
    queue_for(w.gym, day)
    with mock.patch("apps.messages.meta.urlopen", graph):
        return send_due(fresh(w.gym), day)


def retry(graph, at):
    with mock.patch("apps.messages.meta.urlopen", graph):
        return send_retries(at)


# ---- What Meta gets ----

def test_the_payload_is_metas_template_shape(w, cloud, shared_number):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Asha Rao", "9811111117")
    graph = Graph(accepted(7))

    assert remind(w, graph) == {"sent": 1, "failed": 0, "skipped": 0}

    [request] = graph.requests
    assert request.full_url == "https://graph.facebook.com/v23.0/200000000000009/messages" and request.get_method() == "POST"
    assert request.get_header("Authorization") == f"Bearer {SHARED_TOKEN}" and SHARED_TOKEN not in request.full_url
    assert request.get_header("Content-type") == "application/json"
    end = Member.objects.get(pk=member.pk).subscriptions.get().ends
    assert graph.bodies == [{
        "messaging_product": "whatsapp", "recipient_type": "individual", "to": "919811111117", "type": "template",
        "template": {"name": "plan_ending_v1", "language": {"code": "en"}, "components": [{"type": "body", "parameters": [
            {"type": "text", "text": "Asha"}, {"type": "text", "text": "Monthly plan"}, {"type": "text", "text": w.gym.name},
            {"type": "text", "text": clock.date_label(end)}, {"type": "text", "text": "in 7 days"},
        ]}]},
    }]

    row = Message.objects.get(member=member)
    assert row.status == Message.SENT and row.provider == "whatsapp_cloud" and row.provider_id == "wamid.HBgM0007"
    assert row.account == shared_number and row.template.kind == WhatsAppTemplate.PLAN_ENDING and row.attempts == 1
    assert row.parameters == ["Asha", "Monthly plan", w.gym.name, clock.date_label(end), "in 7 days"]
    assert row.text == f"Hi Asha, your Monthly plan at {w.gym.name} ends on {clock.date_label(end)}, in 7 days. Renew it at the front desk to keep checking in."
    assert row.dedupe_key == f"member:{member.id}:reminder:{w.today.isoformat()}"
    assert row.billable and row.rate_paise == w.billing.utility_message_paise == 15  # the gym's rate, from its plan


def test_a_template_without_details_has_no_components():
    template = WhatsAppTemplate(name="hello", language="en_US", body="Hello from Rackline")
    assert template_payload("+919800000001", template, [])["template"] == {"name": "hello", "language": {"code": "en_US"}}


def test_the_words_come_from_the_template(w, shared_number):
    """The record says what the member read: the template's text, filled in, whatever the template says."""
    shared_number.templates.filter(kind=WhatsAppTemplate.PAYMENT_DUE).update(
        body="Namaste {{1}}, {{2}} is due at {{3}}.", parameters=["first_name", "amount", "gym"])
    member = w.plan_ending_on(w.today + timedelta(days=20), "Vikram Shah", "9811111120", paid=False)

    queue_for(w.gym, w.today)
    assert send_due(fresh(w.gym), w.today)["sent"] == 1
    row = Message.objects.get(member=member)
    assert row.text == f"Namaste Vikram, ₹1,500 is due at {w.gym.name}." == FakeSender.outbox[0][1]
    assert row.parameters == ["Vikram", "₹1,500", w.gym.name]


# ---- Which number ----

def test_a_gym_on_its_own_number_sends_from_it(w, other, cloud, shared_number):
    own = accounts.add_account(gym=w.gym, **OWN)
    WhatsAppTemplate.objects.create(account=own, kind=WhatsAppTemplate.PLAN_ENDING, name="renew_soon", language="en",
                                    body="{{1}}, renew by {{2}}.", parameters=["first_name", "end_date"], status=WhatsAppTemplate.APPROVED)
    change_plan(w.gym, whatsapp_mode=GymBilling.OWN)
    mine = w.plan_ending_on(w.today + timedelta(days=7), "On Own", "9811111117")
    theirs = other.plan_ending_on(other.today + timedelta(days=7), "On Shared", "9811111118")
    graph = Graph(accepted(1), accepted(2))

    remind(w, graph)
    queue_for(other.gym, other.today)
    with mock.patch("apps.messages.meta.urlopen", graph):
        send_due(fresh(other.gym), other.today)

    own_call, shared_call = graph.requests
    assert own_call.full_url.endswith("/200000000000002/messages") and own_call.get_header("Authorization") == f"Bearer {OWN['access_token']}"
    assert shared_call.full_url.endswith("/200000000000009/messages") and shared_call.get_header("Authorization") == f"Bearer {SHARED_TOKEN}"
    assert graph.bodies[0]["template"]["name"] == "renew_soon" and graph.bodies[1]["template"]["name"] == "plan_ending_v1"

    on_own = Message.objects.get(member=mine)
    assert on_own.account == own and not on_own.billable and on_own.rate_paise == 0  # the gym pays Meta itself
    on_shared = Message.objects.get(member=theirs)
    assert on_shared.account == shared_number and on_shared.billable


def test_own_mode_without_its_own_number_doesnt_fall_back_to_the_shared_one(w, cloud):
    change_plan(w.gym, whatsapp_mode=GymBilling.OWN)
    member = w.plan_ending_on(w.today + timedelta(days=7), "No Number Yet", "9811111117")
    graph = Graph()

    assert remind(w, graph) == {"sent": 0, "failed": 1, "skipped": 0}
    assert graph.requests == []
    row = Message.objects.get(member=member)
    assert row.status == Message.FAILED and row.account is None and row.error == services.NOT_SET_UP and row.attempts == 0


def test_no_approved_template_says_so_and_sends_nothing(w, cloud, shared_number):
    shared_number.templates.filter(kind=WhatsAppTemplate.PLAN_ENDING).update(status=WhatsAppTemplate.PAUSED)
    member = w.plan_ending_on(w.today + timedelta(days=7), "No Template", "9811111117")
    graph = Graph()

    assert remind(w, graph)["failed"] == 1 and graph.requests == []
    row = Message.objects.get(member=member)
    assert row.status == Message.FAILED and row.error == "Not sent: there's no approved WhatsApp template for plan ending soon yet."


# ---- Who gets nothing ----

def test_a_suspended_gym_sends_nothing(w, cloud):
    w.plan_ending_on(w.today + timedelta(days=7), "Paused Gym", "9811111117")
    suspend(w.gym, "Unpaid invoice")
    graph = Graph()

    assert remind(w, graph) == {"sent": 0, "failed": 0, "skipped": 0}
    assert graph.requests == [] and not Message.objects.exists()


def test_a_gym_with_whatsapp_off_sends_nothing(w, cloud):
    change_plan(w.gym, whatsapp_mode=GymBilling.OFF)
    w.plan_ending_on(w.today + timedelta(days=7), "WhatsApp Off", "9811111117")
    graph = Graph()

    assert remind(w, graph) == {"sent": 0, "failed": 0, "skipped": 0}
    assert graph.requests == [] and not Message.objects.exists()
    assert ReminderDue.objects.filter(gym=w.gym).exists()  # the desk's list is still there


def test_a_wait_for_a_retry_ends_if_the_gym_is_paused_or_switched_off_meanwhile(w, cloud):
    paused = w.plan_ending_on(w.today + timedelta(days=7), "Paused Meanwhile", "9811111117")
    remind(w, Graph(refused(130429, "Rate limit hit")))
    suspend(w.gym, "Unpaid invoice")
    graph = Graph()

    assert retry(graph, timezone.now() + timedelta(minutes=2))["failed"] == 1
    assert graph.requests == []
    assert Message.objects.get(member=paused).status == Message.FAILED and Message.objects.get(member=paused).error == services.PAUSED


def test_someone_who_opts_out_while_waiting_isnt_sent_to(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Changed Mind", "9811111117")
    remind(w, Graph(refused(130429)))
    Member.objects.filter(pk=member.pk).update(reminders_opted_out=True)
    graph = Graph()

    retry(graph, timezone.now() + timedelta(minutes=2))
    assert graph.requests == [] and Message.objects.get(member=member).error == services.OPTED_OUT


# ---- Never twice ----

def test_a_crash_after_the_row_is_written_never_sends_twice(w, cloud):
    """The worker dies after Meta took the message but before its id was kept: nothing sends it again."""
    member = w.plan_ending_on(w.today + timedelta(days=7), "Crash Test", "9811111117")
    graph = Graph()
    real_save = Message.save

    def die(self, *args, **kwargs):
        if kwargs.get("update_fields"):
            raise SystemExit("the worker was killed")
        return real_save(self, *args, **kwargs)

    with mock.patch.object(Message, "save", die), pytest.raises(SystemExit):
        remind(w, graph)
    assert len(graph.requests) == 1
    row = Message.objects.get(member=member)
    assert row.status == Message.QUEUED and row.attempts == 1 and row.provider_id == ""  # written, counted as tried

    assert remind(w, graph) == {"sent": 0, "failed": 0, "skipped": 0}  # the morning's next tick
    assert retry(graph, timezone.now()) == {"sent": 0, "failed": 0, "waiting": 0, "interrupted": 0}  # the retry sweep
    later = retry(graph, timezone.now() + services.INTERRUPTED_AFTER + timedelta(minutes=1))
    assert later["interrupted"] == 1 and later["sent"] == 0
    assert len(graph.requests) == 1  # still the one
    row.refresh_from_db()
    assert row.status == Message.FAILED and row.error == services.INTERRUPTED


def test_two_runs_writing_the_same_message_send_it_once(w, cloud):
    """Two of the morning's ticks at once: whichever writes the row sends it; the other finds it taken."""
    member = w.plan_ending_on(w.today + timedelta(days=7), "Raced", "9811111117")
    queue_for(w.gym, w.today)
    key = Message.reminder_key(member.id, w.today)
    first = Message(gym=w.gym, member=member, kind="plan_ending", dedupe_key=key, to=member.phone, for_date=w.today, provider="x")
    second = Message(gym=w.gym, member=member, kind="plan_ending", dedupe_key=key, to=member.phone, for_date=w.today, provider="x")

    assert services.queue([first]) is True
    assert services.queue([second]) is False
    assert Message.objects.filter(dedupe_key=key).count() == 1


def test_a_retry_is_taken_by_one_run_only(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Taken Once", "9811111117")
    remind(w, Graph(refused(130429)))
    now = timezone.now() + timedelta(minutes=2)
    one, two = Message.objects.get(member=member), Message.objects.get(member=member)

    assert services._claim(one, now) is True and one.attempts == 2
    assert services._claim(two, now) is False  # the second run read it before the first took it


def test_a_meta_timeout_isnt_tried_again(w, cloud):
    """No answer may still mean Meta sent it, so it is never tried again on its own."""
    member = w.plan_ending_on(w.today + timedelta(days=7), "Timed Out", "9811111117")
    graph = Graph(TimeoutError("The read operation timed out"))

    assert remind(w, graph)["failed"] == 1
    row = Message.objects.get(member=member)
    assert row.status == Message.FAILED and row.error_code == "no_answer" and row.next_retry_at is None
    assert retry(graph, timezone.now() + timedelta(hours=1))["sent"] == 0 and len(graph.requests) == 1


# ---- Retries ----

def test_temporary_errors_retry_three_times_with_growing_waits_then_stop(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Rate Limited", "9811111117")
    graph = Graph(refused(130429, "Rate limit hit"))
    start = timezone.now()

    assert remind(w, graph) == {"sent": 0, "failed": 1, "skipped": 0}
    row = Message.objects.get(member=member)
    assert row.status == Message.QUEUED and row.attempts == 1 and row.error_code == "130429"
    assert row.error == "Rate limit hit (code 130429)"
    waits = [row.next_retry_at - start]

    assert retry(graph, row.next_retry_at - timedelta(seconds=1))["waiting"] == 0  # not yet
    assert len(graph.requests) == 1
    for attempt in (2, 3, 4):
        at = row.next_retry_at
        retry(graph, at)
        row.refresh_from_db()
        assert row.attempts == attempt and len(graph.requests) == attempt
        if row.next_retry_at:
            waits.append(row.next_retry_at - at)

    assert row.status == Message.FAILED and row.next_retry_at is None and row.error_code == "130429"
    assert [round(wait.total_seconds() / 60) for wait in waits] == [1, 5, 15]
    retry(graph, timezone.now() + timedelta(days=1))
    assert len(graph.requests) == 4  # 1 try and 3 retries, and that's all


def test_a_retry_that_gets_through_is_sent(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Second Time Lucky", "9811111117")
    graph = Graph(URLError("Connection refused"), accepted(9))

    remind(w, graph)
    row = Message.objects.get(member=member)
    assert row.status == Message.QUEUED and row.error_code == "unreachable"

    assert retry(graph, row.next_retry_at) == {"sent": 1, "failed": 0, "waiting": 0, "interrupted": 0}
    row.refresh_from_db()
    assert row.status == Message.SENT and row.provider_id == "wamid.HBgM0009" and row.error == "" and row.attempts == 2


@pytest.mark.parametrize("error", [
    refused(131026, "Message undeliverable"), refused(132001, "Template name does not exist in the translation"),
    refused(190, "Invalid OAuth access token", status=401),
])
def test_permanent_errors_fail_at_once(w, cloud, error):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Not Again", "9811111117")
    graph = Graph(error)

    remind(w, graph)
    row = Message.objects.get(member=member)
    assert row.status == Message.FAILED and row.next_retry_at is None and row.attempts == 1
    assert retry(graph, timezone.now() + timedelta(hours=2))["sent"] == 0 and len(graph.requests) == 1


def test_meta_being_down_is_temporary(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Meta Down", "9811111117")
    down = HTTPError("https://graph.facebook.com/x", 503, "Service Unavailable", hdrs=None, fp=io.BytesIO(b"<html>"))
    remind(w, Graph(down))
    row = Message.objects.get(member=member)
    assert row.status == Message.QUEUED and row.error_code == "503" and row.error == "Meta answered 503"


def test_metas_reason_never_carries_a_credential(w, cloud):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Echoed Token", "9811111117")
    remind(w, Graph(refused(190, f"Token {SHARED_TOKEN} has expired", status=401)))
    row = Message.objects.get(member=member)
    assert SHARED_TOKEN not in row.error and row.error == "Token … has expired (code 190)"


def test_the_jobs_run_as_beat_runs_them(w, cloud):
    """The morning job and the retry sweep, as the worker runs them (eager here, as no broker is set)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    day = datetime(2026, 6, 1).date()
    member = w.plan_ending_on(day + timedelta(days=3), "Three Days", "9811111113")
    graph = Graph(refused(131000, "Something went wrong"), accepted(3))
    with mock.patch("apps.messages.meta.urlopen", graph):
        assert send_reminders.apply(kwargs={"at": datetime(2026, 6, 1, 0, 30, tzinfo=ZoneInfo("UTC")).isoformat()}).get() == 0
        row = Message.objects.get(member=member)
        assert retry_messages.apply(kwargs={"at": row.next_retry_at.isoformat()}).get() == 1
    row.refresh_from_db()
    assert row.status == Message.SENT and row.for_date == day


# ---- The words stay the same for members ----

def test_reminders_read_the_same_as_before(w, shared_number):
    """The demo templates say what the built-in words said, so members see no change."""
    member = w.plan_ending_on(w.today + timedelta(days=1), "Tomorrow Person", "9811111117")
    queue_for(w.gym, w.today)
    # 1 day ahead isn't a reminder day; write one by hand to see the "tomorrow" wording
    ReminderDue.objects.create(gym=w.gym, member=member, kind=ReminderDue.PLAN_ENDING, days_left=1, for_date=w.today)
    send_due(fresh(w.gym), w.today)
    assert ", tomorrow. Renew it at the front desk" in Message.objects.get(member=member).text


# ---- Messages from before ----

@pytest.mark.django_db(transaction=True)
def test_messages_already_on_record_get_their_reminders_key(w):
    """The migration gives every earlier message the key its reminder would have now, so none can go again."""
    from datetime import date

    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    # Back to before the keys, then forward to the latest of every app (going back undoes the gyms migration that
    # needs the messages' latest): the model below is today's, with every later column
    before, after = [("gym_messages", "0002_whatsapp_accounts")], executor.loader.graph.leaf_nodes()
    executor.migrate(before)
    OldMessage = executor.loader.project_state(before).apps.get_model("gym_messages", "Message")
    OldMessage.objects.create(gym_id=w.gym.id, member_id=w.member.id, kind="dues", to=w.member.phone, text="Hi Asha",
                              for_date=date(2026, 5, 4), status="sent", provider="fake", provider_id="fake-1")
    executor = MigrationExecutor(connection)
    executor.migrate(after)

    row = Message.objects.get()
    assert row.dedupe_key == Message.reminder_key(w.member.id, date(2026, 5, 4)) == f"member:{w.member.id}:reminder:2026-05-04"
    assert row.status == Message.SENT and row.attempts == 1 and row.text == "Hi Asha" and row.parameters == []
    assert row.account is None and not row.billable
    assert row.kind == "payment_due"  # the reminder kinds became their messages' kinds
