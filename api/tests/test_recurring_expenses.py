from datetime import date, timedelta

from apps.audit.models import AuditLog
from apps.core import clock
from apps.expenses.models import Expense, ExpenseDue, RecurringExpense

URL = "/api/recurring-expenses/"
DUES = "/api/expense-dues/"


def rule(w, starts, frequency="monthly", paise=85_000_00, remind=3, ends=None, branch=None, name="Rent"):
    return RecurringExpense.objects.create(gym=w.gym, branch=branch or w.a, name=name, category="rent", amount_paise=paise, method="bank",
                                           paid_to="Landlord", frequency=frequency, starts=starts, ends=ends, remind_days=remind, created_by=w.admin)


def body(w, **kw):
    return {"branch": w.a.id, "name": "Electricity", "category": "utilities", "amount_paise": 18_500_00, "method": "upi", "paid_to": "BESCOM",
            "frequency": "monthly", "starts": w.today.isoformat(), "remind_days": 3, **kw}


def test_dates_keep_their_day_through_short_months():
    r = RecurringExpense(starts=date(2026, 1, 31), frequency="monthly")
    assert r.due_dates(None, date(2026, 4, 30)) == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]
    assert r.due_dates(date(2026, 2, 28), date(2026, 3, 31)) == [date(2026, 3, 31)]
    weekly = RecurringExpense(starts=date(2026, 10, 1), frequency="weekly", ends=date(2026, 10, 20))
    assert weekly.due_dates(None, date(2026, 12, 31)) == [date(2026, 10, 1), date(2026, 10, 8), date(2026, 10, 15)]
    yearly = RecurringExpense(starts=date(2024, 2, 29), frequency="yearly")
    assert yearly.due_dates(None, date(2028, 3, 1)) == [date(2024, 2, 29), date(2025, 2, 28), date(2026, 2, 28), date(2027, 2, 28), date(2028, 2, 29)]


def test_admin_adds_one_and_its_dates_are_written(w):
    c = w.client(w.admin)
    r = c.post(URL, body(w, starts=(w.today + timedelta(days=2)).isoformat()), format="json")
    assert r.status_code == 201, r.json()
    assert r.json()["next_due"] == (w.today + timedelta(days=2)).isoformat() and r.json()["is_active"] is True
    rule_ = RecurringExpense.objects.get(id=r.json()["id"])
    assert rule_.created_by == w.admin and AuditLog.objects.filter(action="recurring_expense.added", object_id=str(rule_.id)).exists()
    # Due in 2 days, reminder 3 days before: it is open now; next month's is upcoming.
    open_ = c.get(DUES).json()["results"]
    assert [(d["name"], d["state"], d["amount_paise"]) for d in open_] == [("Electricity", "soon", 18_500_00)]
    upcoming = c.get(DUES, {"state": "upcoming"}).json()["results"]
    assert upcoming and all(d["state"] == "later" for d in upcoming)


def test_reading_twice_writes_nothing_new(w):
    rule(w, w.today - timedelta(days=40))
    c = w.client(w.admin)
    c.get(DUES)
    n = ExpenseDue.objects.count()
    c.get(DUES)
    c.get("/api/reports/summary/")
    assert ExpenseDue.objects.count() == n and n >= 2


def test_pay_a_due_with_its_own_amount(w):
    r = rule(w, w.today - timedelta(days=1), paise=18_500_00)
    c = w.client(w.admin)
    due = c.get(DUES).json()["results"][0]
    assert due["state"] == "overdue"
    paid = c.post(f"{DUES}{due['id']}/pay/", {"amount_paise": 19_200_00, "method": "upi"}, format="json")
    assert paid.status_code == 200, paid.json()
    assert paid.json()["status"] == "paid" and paid.json()["paid_paise"] == 19_200_00 and paid.json()["paid_on"] == w.today.isoformat()
    e = Expense.objects.get(due__id=due["id"])
    assert (e.category, e.branch, e.amount_paise, e.paid_to, e.created_by) == ("rent", w.a, 19_200_00, "Landlord", w.admin)
    assert c.post(f"{DUES}{due['id']}/pay/", {"amount_paise": 100, "method": "upi"}, format="json").json()["error"]["code"] == "not_due"
    assert AuditLog.objects.filter(action="expense_due.paid", object_id=str(due["id"])).exists()
    # It counts as an expense, and it can only be changed from Dues.
    listed = c.get("/api/expenses/").json()["results"]
    assert listed[0]["paid_for"] == "bill"
    assert c.patch(f"/api/expenses/{e.id}/", {"note": "x"}, format="json").json()["error"]["code"] == "paid_a_bill"
    assert c.delete(f"/api/expenses/{e.id}/").status_code == 409
    assert r.dues.filter(status="paid").count() == 1


def test_pay_checks_the_amount_and_day(w):
    rule(w, w.today)
    c = w.client(w.admin)
    due = c.get(DUES).json()["results"][0]
    assert c.post(f"{DUES}{due['id']}/pay/", {"amount_paise": 0, "method": "upi"}, format="json").status_code == 400
    tomorrow = (w.today + timedelta(days=1)).isoformat()
    assert c.post(f"{DUES}{due['id']}/pay/", {"amount_paise": 100, "method": "upi", "paid_on": tomorrow}, format="json").status_code == 400


def test_skip_leaves_the_list_and_spends_nothing(w):
    rule(w, w.today)
    c = w.client(w.admin)
    due = c.get(DUES).json()["results"][0]
    assert c.post(f"{DUES}{due['id']}/skip/").json()["status"] == "skipped"
    assert c.get(DUES).json()["results"] == [] and not Expense.objects.exists()
    assert c.post(f"{DUES}{due['id']}/skip/").json()["error"]["code"] == "not_due"
    assert [d["id"] for d in c.get(DUES, {"state": "skipped"}).json()["results"]] == [due["id"]]


def test_stop_skips_the_dates_still_to_come(w):
    r = rule(w, w.today - timedelta(days=31), remind=40)  # last month's is late, this month's and next month's are listed
    c = w.client(w.admin)
    c.get(DUES)
    late = r.dues.filter(due_on__lt=w.today).count()
    assert c.post(f"{URL}{r.id}/stop/").json()["is_active"] is False
    assert r.dues.filter(status="due").count() == late  # late ones stay to be paid
    assert not r.dues.filter(status="due", due_on__gte=w.today).exists()
    assert c.post(f"{URL}{r.id}/stop/").status_code == 409
    assert c.patch(f"{URL}{r.id}/", {"amount_paise": 100}, format="json").json()["error"]["code"] == "stopped"
    assert AuditLog.objects.filter(action="recurring_expense.stopped").exists()


def test_a_change_reaches_the_dates_still_to_come_only(w):
    r = rule(w, w.today - timedelta(days=31), remind=40, paise=10_000_00)
    c = w.client(w.admin)
    c.get(DUES)
    past = r.dues.filter(due_on__lt=w.today).first()
    assert c.patch(f"{URL}{r.id}/", {"amount_paise": 12_000_00, "remind_days": 5}, format="json").status_code == 200
    later = r.dues.filter(due_on__gte=w.today)
    assert later.exists() and all(d.amount_paise == 12_000_00 and d.remind_on == d.due_on - timedelta(days=5) for d in later)
    past.refresh_from_db()
    assert past.amount_paise == 10_000_00
    # Dates are fixed once it's due; ending it sooner skips the dates past its end.
    assert c.patch(f"{URL}{r.id}/", {"starts": w.today.isoformat()}, format="json").status_code == 400
    assert c.patch(f"{URL}{r.id}/", {"ends": (w.today - timedelta(days=60)).isoformat()}, format="json").status_code == 400
    c.patch(f"{URL}{r.id}/", {"ends": w.today.isoformat()}, format="json")
    assert not r.dues.filter(status="due", due_on__gt=w.today).exists()


def test_only_admins_and_only_this_gym(w, other):
    r = rule(w, w.today)
    w.client(w.admin).get(DUES)
    due = r.dues.first()
    for role in (w.desk, w.trainer):
        assert w.client(role).get(URL).status_code == 403
        assert w.client(role).get(DUES).status_code == 403
        assert w.client(role).post(f"{DUES}{due.id}/pay/", {"amount_paise": 100, "method": "cash"}, format="json").status_code == 403
    assert w.member_client().get(DUES).status_code == 403
    them = other.client(other.admin)
    assert them.get(f"{URL}{r.id}/").status_code == 404
    assert them.post(f"{DUES}{due.id}/pay/", {"amount_paise": 100, "method": "cash"}, format="json").status_code == 404
    assert them.get(DUES).json()["results"] == []
    # Another gym's branch is refused on create.
    assert w.client(w.admin).post(URL, body(w, branch=other.a.id), format="json").status_code == 400


def test_branch_filter(w):
    rule(w, w.today, name="Rent A")
    rule(w, w.today, branch=w.b, name="Rent B")
    c = w.client(w.admin)
    assert [d["name"] for d in c.get(DUES, {"branch": w.b.id}).json()["results"]] == ["Rent B"]
    assert c.get(f"{DUES}summary/", {"branch": w.b.id}).json() == {"count": 1, "overdue": 0, "total_paise": 85_000_00}


def test_home_counts_bills_and_salaries(w):
    rule(w, w.today - timedelta(days=2), paise=50_000_00)  # late
    rule(w, w.today + timedelta(days=10), paise=1_000_00, name="Software")  # not yet inside its 3 days
    dues = w.client(w.admin).get("/api/reports/summary/").json()["expense_dues"]
    assert dues == {"count": 1, "overdue_bills": 1, "bills": 1, "salaries": 0, "total_paise": 50_000_00}


def test_lists_keep_to_a_query_budget(w, django_assert_max_num_queries):
    for i in range(6):
        rule(w, w.today - timedelta(days=i), name=f"Bill {i}")
    c = w.client(w.admin)
    c.get(DUES)
    with django_assert_max_num_queries(12):
        assert len(c.get(DUES).json()["results"]) == 6
    with django_assert_max_num_queries(10):
        assert len(c.get(URL).json()["results"]) == 6
    assert clock.today(w.gym) == w.today
