"""Console → Home: Rackline at a glance, for Rackline admins only, in a fixed number of queries."""
from datetime import date, datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import BranchRequest, Invoice, InvoicePayment
from apps.core.models import JobRun
from apps.gyms.models import Gym, SupportAccess
from apps.messages.models import Message
from apps.platform.summary import summary
from tests.conftest import World
from tests.test_platform import rackline, support
from tests.test_server import message, on_a_server  # noqa: F401 (a fixture)

HOME = "/api/platform/summary/"
GYMS = "/api/platform/gyms/"
IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 10, 19, 14, 0, tzinfo=IST)  # a Monday afternoon, Rackline's day 19 Oct
TODAY = NOW.date()


def invoice(w, n, total, due_on, status=Invoice.OPEN):
    return Invoice.objects.create(gym=w.gym, number=f"RL/{w.gym.pk}/{n}", period_from=date(2025, 1, 1) + timedelta(days=40 * n),
                                  period_to=due_on + timedelta(days=20), issued_on=due_on - timedelta(days=7), due_on=due_on,
                                  status=status, subtotal_paise=total, total_paise=total)


def payment(w, inv, amount, voided=False):
    return InvoicePayment.objects.create(gym=w.gym, invoice=inv, receipt_number=f"RLR/{inv.pk}/{amount}", amount_paise=amount,
                                         method="upi", paid_on=TODAY, recorded_by=w.admin.user, voided=voided)


def ask(w):
    return BranchRequest.objects.create(gym=w.gym, count=1, asked_by=w.admin.user)


def delivered(w, n, at, billable=False, rate=0):
    return message(w, Message.DELIVERED, f"d{n}", delivered_at=at, billable=billable, rate_paise=rate)


def run(job, error="", finished=True):
    at = NOW - timedelta(hours=1)
    return JobRun.objects.create(job=job, started_at=at, finished_at=at + timedelta(seconds=3) if finished else None, error=error)


# ---- who may look ----

def test_only_rackline_admins_see_home(w):
    SupportAccess.objects.create(gym=w.gym, granted_by=w.admin.user, starts=timezone.now() - timedelta(minutes=5),
                                 ends=timezone.now() + timedelta(hours=1))
    for c in (w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client(), support()):
        assert c.get(HOME, HTTP_X_GYM=w.gym.slug).status_code == 403
        assert c.get(HOME).status_code == 403
    assert APIClient().get(HOME).status_code == 401
    assert rackline().get(HOME).status_code == 200


# ---- what it counts ----

@pytest.fixture
def busy(w, other):
    """Three gyms, their invoices and requests, a month of messages, and the jobs' last runs, around NOW."""
    late = World("late", 2)
    Gym.objects.filter(pk=late.gym.pk).update(status=Gym.SUSPENDED)
    Gym.objects.filter(pk__in=[w.gym.pk, other.gym.pk]).update(created_at=datetime(2026, 9, 2, tzinfo=IST))
    Gym.objects.filter(pk=late.gym.pk).update(created_at=datetime(2026, 10, 1, 0, 5, tzinfo=IST))
    Gym.objects.create(name="Fresh Fitness", slug="fresh")  # on trial, added today, owes nothing

    overdue = invoice(w, 1, 250000, TODAY - timedelta(days=1))  # due yesterday: ₹2,500, ₹1,000 paid
    payment(w, overdue, 100000)
    payment(w, overdue, 50000, voided=True)  # voided: still owed
    invoice(w, 2, 180000, TODAY)  # due today: owed, not overdue yet
    invoice(w, 3, 99900, TODAY - timedelta(days=30), status=Invoice.PAID)
    invoice(w, 4, 77700, TODAY - timedelta(days=30), status=Invoice.VOID)
    invoice(late, 1, 120000, TODAY - timedelta(days=12))
    invoice(late, 2, 120000, TODAY - timedelta(days=40))

    ask(w)
    ask(other)
    BranchRequest.objects.create(gym=late.gym, count=2, asked_by=late.admin.user, status=BranchRequest.DECLINED)

    month = datetime(2026, 10, 1, 0, 1, tzinfo=IST)
    delivered(w, 1, NOW - timedelta(hours=2), billable=True, rate=15)
    delivered(other, 2, datetime(2026, 10, 19, 0, 10, tzinfo=IST))  # today, on a gym's own number
    delivered(w, 3, month, billable=True, rate=15)
    delivered(other, 4, month + timedelta(days=5), billable=True, rate=80)
    delivered(w, 5, datetime(2026, 9, 30, 23, 50, tzinfo=IST), billable=True, rate=15)  # last month
    message(w, Message.FAILED, 1)  # failed today
    old = message(other, Message.FAILED, 2)
    Message.objects.filter(pk=old.pk).update(updated_at=NOW - timedelta(days=1))
    message(w, Message.QUEUED, 7, next_retry_at=NOW + timedelta(minutes=5))

    run(JobRun.REMINDERS, error="ConnectionError: Meta didn't answer")
    run(JobRun.INVOICES, error="IntegrityError")
    run(JobRun.INVOICES, finished=False)  # running again now: not counted as failed
    run(JobRun.RETRIES)
    return late


def test_home_counts_gyms_money_requests_messages_and_jobs(w, other, busy):
    s = summary(NOW)

    assert s["gyms"] == {"active": 2, "trial": 1, "suspended": 1, "new_this_month": 2}
    assert s["money"] == {
        "owed_paise": 150000 + 180000 + 240000, "gyms_owing": 2,
        "overdue_paise": 150000 + 240000, "overdue_invoices": 3, "gyms_overdue": 2,
    }
    assert s["branch_requests"] == {"waiting": 2}
    assert s["whatsapp"] == {"delivered_today": 2, "failed_today": 1, "waiting_retry": 1, "shared_messages": 3, "shared_paise": 110}
    assert s["server"]["down"] == []  # no broker in the tests: Redis, the worker and beat are off, not down
    assert [(j["job"], j["last_run"].error) for j in s["server"]["failed_jobs"]] == [("reminders", "ConnectionError: Meta didn't answer")]


def test_home_shows_what_is_down(w, on_a_server):  # noqa: F811
    on_a_server.return_value = []  # the worker doesn't answer, and beat has never ticked
    s = summary(NOW)
    assert [(c.key, c.detail) for c in s["server"]["down"]] == [("worker", "No answer in 2 seconds"), ("beat", "No tick yet")]


def test_home_with_nothing_yet(db):
    s = summary(NOW)
    assert s["gyms"] == {"active": 0, "trial": 0, "suspended": 0, "new_this_month": 0}
    assert set(s["money"].values()) == {0}
    assert s["server"]["failed_jobs"] == [] and s["branch_requests"] == {"waiting": 0}


def test_home_is_counts_and_rackline_money_only_within_a_query_budget(w, other, busy, django_assert_max_num_queries):
    c = rackline()
    with django_assert_max_num_queries(11):
        r = c.get(HOME)
    assert r.status_code == 200, r.content
    body = r.json()
    assert set(body) == {"checked_at", "gyms", "money", "branch_requests", "whatsapp", "server"}
    assert body["server"]["failed_jobs"][0] == {"job": "reminders", "label": "Reminders", "error": "ConnectionError: Meta didn't answer",
                                                "finished_at": body["server"]["failed_jobs"][0]["finished_at"]}
    text = r.content.decode()
    for inside in (w.member.name, w.member.phone, "Hi Asha", w.admin.user.email):  # no member, message words or staff
        assert inside not in text

    for n in range(3, 8):  # more gyms, each with an overdue invoice and a request: the same queries
        more = World(f"more{n}", n)
        invoice(more, 1, 50000, date(2026, 1, 1))
        ask(more)
    with CaptureQueriesContext(connection) as before:
        c.get(HOME)
    with django_assert_max_num_queries(len(before)):
        assert c.get(HOME).json()["branch_requests"]["waiting"] == 7


# ---- the gyms it links to ----

def test_the_gyms_list_shows_the_gyms_that_owe(w, other, busy):
    c = rackline()
    names = lambda q: {g["name"] for g in c.get(GYMS, q).json()["results"]}  # noqa: E731
    with mock.patch("apps.platform.queries.timezone.localdate", return_value=TODAY):
        assert names({"owes": "any"}) == {w.gym.name, busy.gym.name}
        assert names({"owes": "overdue"}) == {w.gym.name, busy.gym.name}
        assert names({"owes": "overdue", "status": "suspended"}) == {busy.gym.name}
        Invoice.objects.filter(gym=w.gym, due_on__lt=TODAY, status=Invoice.OPEN).update(due_on=TODAY)
        assert names({"owes": "overdue"}) == {busy.gym.name}
        assert names({"owes": "any"}) == {w.gym.name, busy.gym.name}
    r = c.get(GYMS, {"owes": "lots"})
    assert r.status_code == 400 and "owes" in r.json()["error"]["fields"]

