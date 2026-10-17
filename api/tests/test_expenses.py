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
