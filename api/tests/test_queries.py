"""Query budgets: a list costs the same number of queries for 2 rows as for 20. An N+1 fails here."""
from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.attendance.models import CheckIn
from apps.attendance.services import check_in
from apps.expenses.models import Expense
from apps.members.models import Member
from apps.tasks.models import Task
from apps.members.services import sell, take_payment


def grow(w, n):
    """n more members at branch A, each with a plan, a part payment and a check-in today."""
    start = Member.objects.filter(gym=w.gym).count()
    for i in range(start, start + n):
        m = w.new_member(f"Extra {i}", f"97{5000 + i:08d}", w.a, trainer=w.trainer)
        sub = sell(m, w.monthly, by=w.desk, starts=w.today - timedelta(days=2))
        take_payment(m, sub.price_paise // 2, "cash", by=w.desk)
        check_in(w.a, member=m, source=CheckIn.DESK)
        Task.objects.create(gym=w.gym, title=f"Task {i}", assignee=w.desk, created_by=w.admin, due_date=w.today)
        Expense.objects.create(gym=w.gym, branch=w.a, category="other", amount_paise=1000, spent_on=w.today, created_by=w.admin)


def queries(client, url):
    with CaptureQueriesContext(connection) as q:
        r = client.get(url)
    assert r.status_code == 200, r.content
    return len(q)


LISTS = [
    ("admin", "/api/members/"),
    ("admin", "/api/members/?status=due"),
    ("trainer", "/api/members/"),
    ("admin", "/api/reports/summary/"),
    ("admin", "/api/subscriptions/"),
    ("admin", "/api/payments/"),
    ("desk", "/api/checkins/"),
    ("desk", "/api/checkins/summary/"),
    ("admin", "/api/tasks/"),
    ("admin", "/api/tasks/counts/"),
    ("admin", "/api/expenses/"),
    ("admin", "/api/staff/"),
]


@pytest.mark.parametrize("who,url", LISTS)
def test_list_queries_dont_grow_with_rows(w, who, url):
    client = w.client(getattr(w, who))
    grow(w, 2)
    small = queries(client, url)
    grow(w, 10)
    assert queries(client, url) == small, f"{url} runs more queries with more rows: an N+1"


@pytest.mark.parametrize("who,url", LISTS)
def test_list_query_budget(w, who, url):
    grow(w, 5)
    assert queries(w.client(getattr(w, who)), url) <= 12


def test_listed_status_and_balance_match_single_member(w):
    """The annotated list and the one-member path must agree, or screens disagree with check-in."""
    grow(w, 3)
    rows = {r["id"]: r for r in w.client(w.admin).get("/api/members/").json()["results"]}
    for m in Member.objects.filter(gym=w.gym):
        assert rows[m.id]["status"] == m.status(w.today)
        assert rows[m.id]["balance_paise"] == m.balance_paise()
