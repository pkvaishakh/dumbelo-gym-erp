from datetime import timedelta

from apps.expenses.models import Expense
from apps.tasks.models import Task

URL = "/api/reports/period/"


def task(w, who, due, status=Task.TODO, title="Restock towels"):
    return Task.objects.create(gym=w.gym, title=title, assignee=who, created_by=w.admin, due_date=due, status=status)


def test_period_totals_and_series(w):
    Expense.objects.create(gym=w.gym, branch=w.a, category="rent", method="cash", amount_paise=40000, spent_on=w.today, created_by=w.admin)
    r = w.client(w.admin).get(URL).json()
    assert r["days"] == 7 and r["to"] == w.today.isoformat()
    assert r["totals"]["revenue_paise"] == 150000 and r["totals"]["expenses_paise"] == 40000 and r["totals"]["new_members"] == 1
    assert len(r["series"]) == 7 and r["series"][-1]["revenue_paise"] == 150000 and sum(d["revenue_paise"] for d in r["series"]) == 150000
    assert r["revenue_by_plan"] == [{"name": "Monthly", "paise": 150000}]
    assert r["expenses_by_category"] == [{"category": "rent", "label": "Rent", "paise": 40000}]
    assert r["previous"]["to"] == (w.today - timedelta(days=7)).isoformat() and r["previous"]["revenue_paise"] == 0


def test_period_takes_a_range(w):
    first = w.today - timedelta(days=29)
    r = w.client(w.admin).get(URL, {"from": first.isoformat(), "to": w.today.isoformat()}).json()
    assert r["days"] == 30 and len(r["series"]) == 30 and r["previous"]["from"] == (first - timedelta(days=30)).isoformat()
    older = w.client(w.admin).get(URL, {"from": (w.today - timedelta(days=60)).isoformat(), "to": (w.today - timedelta(days=31)).isoformat()}).json()
    assert older["totals"]["revenue_paise"] == 0


def test_period_tasks(w):
    yesterday = w.today - timedelta(days=1)
    task(w, w.trainer, yesterday, Task.DONE, "Call lapsed members")
    late = task(w, w.trainer, yesterday, Task.DOING, "Fix the leg press")
    task(w, w.desk_b, w.today + timedelta(days=1), title="Too late for this period")
    task(w, w.desk_b, w.today - timedelta(days=2), title="Count the towels")
    t = w.client(w.admin).get(URL).json()["tasks"]
    assert (t["total"], t["done"], t["doing"], t["todo"], t["overdue"]) == (3, 1, 1, 1, 2)
    assert t["people"][0]["name"] == w.trainer.user.name and (t["people"][0]["total"], t["people"][0]["done"]) == (2, 1)
    # Oldest due first: the towels were due two days ago, the leg press yesterday.
    assert [x["title"] for x in t["late"]] == ["Count the towels", "Fix the leg press"] and t["late"][1]["id"] == late.id
    assert w.client(w.admin).get(URL).json()["totals"]["tasks_done"] == 1


def test_period_branch_filter(w):
    task(w, w.trainer, w.today)
    task(w, w.desk_b, w.today)
    Expense.objects.create(gym=w.gym, branch=w.b, category="rent", method="cash", amount_paise=40000, spent_on=w.today, created_by=w.admin)
    b = w.client(w.admin).get(URL, {"branch": w.b.id}).json()
    assert b["totals"]["revenue_paise"] == 0 and b["totals"]["expenses_paise"] == 40000 and b["totals"]["new_members"] == 0
    assert b["tasks"]["total"] == 1 and b["tasks"]["people"][0]["name"] == w.desk_b.user.name
    a = w.client(w.admin).get(URL, {"branch": w.a.id}).json()
    assert a["totals"]["revenue_paise"] == 150000 and a["tasks"]["total"] == 1


def test_period_renewals(w):
    from apps.members.services import sell

    sell(w.member, w.monthly, by=w.desk)
    assert w.client(w.admin).get(URL).json()["totals"]["renewals"] == 1


def test_period_bad_input(w):
    c = w.client(w.admin)
    assert c.get(URL, {"from": "yesterday"}).json()["error"]["fields"]["from"]
    assert c.get(URL, {"to": "2026-13-01"}).status_code == 400
    assert c.get(URL, {"from": w.today.isoformat(), "to": (w.today - timedelta(days=1)).isoformat()}).json()["error"]["fields"]["from"]
    assert c.get(URL, {"from": (w.today - timedelta(days=400)).isoformat()}).status_code == 400
    assert c.get(URL, {"branch": "abc"}).status_code == 400


def test_period_roles_and_isolation(w, other):
    for who in (w.desk, w.trainer):
        assert w.client(who).get(URL).status_code == 403
    assert w.member_client().get(URL).status_code == 403
    stranger = other.client(other.admin)
    stranger.credentials(HTTP_X_GYM=w.gym.slug)
    assert stranger.get(URL).status_code == 404
    # Another gym's branch id narrows to nothing; it never reaches their rows.
    assert w.client(w.admin).get(URL, {"branch": other.a.id}).json()["totals"]["revenue_paise"] == 0


def test_period_query_budget(w, django_assert_max_num_queries):
    for i in range(6):
        task(w, w.trainer if i % 2 else w.desk, w.today - timedelta(days=i % 3), title=f"Task {i}")
        w.new_member(f"New {i}", f"97000011{i:02d}", w.a)
    with django_assert_max_num_queries(24):
        assert w.client(w.admin).get(URL, {"from": (w.today - timedelta(days=89)).isoformat()}).status_code == 200
