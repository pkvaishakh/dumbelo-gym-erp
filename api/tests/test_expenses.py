from datetime import timedelta

from apps.expenses.models import Expense

URL = "/api/expenses/"


def spend(w, days_ago, category="rent", branch=None, method="cash", paid_to="", note="", paise=40000):
    return Expense.objects.create(gym=w.gym, branch=branch or w.a, category=category, method=method, paid_to=paid_to, note=note,
                                  amount_paise=paise, spent_on=w.today - timedelta(days=days_ago), created_by=w.admin)


def test_range_search_and_filters(w):
    spend(w, 0, paid_to="Sharma Electricals", category="utilities", method="upi")
    spend(w, 10, note="Dumbbell rack", category="equipment", branch=w.b, paise=90000)
    spend(w, 40, paid_to="Landlord")
    c = w.client(w.admin)
    ids = lambda params: sorted(e["category"] for e in c.get(URL, params).json()["results"])  # noqa: E731
    week = {"from": (w.today - timedelta(days=6)).isoformat(), "to": w.today.isoformat()}
    assert ids(week) == ["utilities"]
    assert ids({"from": (w.today - timedelta(days=30)).isoformat()}) == ["equipment", "utilities"]
    assert ids({"to": (w.today - timedelta(days=30)).isoformat()}) == ["rent"]
    assert ids({"q": "sharma"}) == ["utilities"]  # paid to
    assert ids({"q": "rack"}) == ["equipment"]  # note
    assert ids({"branch": w.b.id}) == ["equipment"]
    assert ids({"method": "upi"}) == ["utilities"]
    assert ids({"category": "rent"}) == ["rent"]
    # Totals follow the same filters.
    t = c.get(URL + "totals/", {"from": (w.today - timedelta(days=30)).isoformat()}).json()
    assert t == {"total_paise": 130000, "by_category": {"equipment": 90000, "utilities": 40000}}


def test_range_must_run_forwards(w):
    r = w.client(w.admin).get(URL, {"from": w.today.isoformat(), "to": (w.today - timedelta(days=1)).isoformat()})
    assert r.status_code == 400 and "from" in r.json()["error"]["fields"]
    assert w.client(w.admin).get(URL, {"from": "yesterday"}).status_code == 400


def test_desk_sees_todays_total_in_its_branches(w):
    spend(w, 0, paise=30000)                 # today, branch A
    spend(w, 0, branch=w.b, paise=90000)     # today, branch B: not the A desk's
    spend(w, 1, paise=50000)                 # yesterday
    desk = w.client(w.desk)
    assert desk.get(URL + "today/").json() == {"date": w.today.isoformat(), "total_paise": 30000, "count": 1}
    assert desk.get(URL + "today/", {"branch": w.b.id}).json()["total_paise"] == 0
    assert w.client(w.admin).get(URL + "today/").json()["total_paise"] == 120000
    assert w.client(w.trainer).get(URL + "today/").status_code == 403
    assert w.client(w.trainer).get(URL).status_code == 403


def test_desk_sees_one_day_of_its_branches_expenses(w):
    spend(w, 0, paise=30000)                 # today, branch A
    spend(w, 0, branch=w.b, paise=90000)     # today, branch B: not the A desk's
    old = spend(w, 1, paise=50000)           # yesterday
    desk = w.client(w.desk)
    amounts = lambda params=None: [e["amount_paise"] for e in desk.get(URL, params).json()["results"]]  # noqa: E731
    assert amounts() == [30000]  # no day given: today
    yesterday = (w.today - timedelta(days=1)).isoformat()
    assert amounts({"from": yesterday, "to": yesterday}) == [50000]
    assert desk.get(URL + "totals/", {"from": yesterday, "to": yesterday}).json()["total_paise"] == 50000
    # Longer spans, months and the other branch's expenses stay with admins.
    assert desk.get(URL, {"from": yesterday, "to": w.today.isoformat()}).status_code == 409
    assert desk.get(URL, {"month": w.today.strftime("%Y-%m")}).status_code == 409
    assert desk.get(URL, {"branch": w.b.id}).json()["results"] == []
    assert w.client(w.desk_b).get(f"{URL}{old.id}/").status_code == 404
    # Editing and removing stay admin-only.
    assert desk.patch(f"{URL}{old.id}/", {"note": "x"}, format="json").status_code == 403
    assert desk.delete(f"{URL}{old.id}/").status_code == 403


def test_desk_adds_expenses_for_its_own_branches(w):
    desk = w.client(w.desk)
    body = {"category": "supplies", "amount_paise": 25000, "method": "cash", "spent_on": w.today.isoformat()}
    r = desk.post(URL, {**body, "branch": w.a.id}, format="json")
    assert r.status_code == 201 and Expense.objects.get(id=r.json()["id"]).created_by == w.desk
    assert desk.post(URL, {**body, "branch": w.b.id}, format="json").status_code == 400
