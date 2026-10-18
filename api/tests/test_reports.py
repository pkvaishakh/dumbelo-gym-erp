"""Reports: one endpoint per category, each over the range and branch asked for, at most 3 months."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.attendance.models import CheckIn
from apps.core import clock
from apps.expenses.models import Expense, RecurringExpense
from apps.expenses.services import pay_due, sync_dues
from apps.finance import services as money
from apps.finance.models import Account, DrawerClose, MoneyMove, Reconciliation
from apps.gyms.models import SupportAccess
from apps.members.services import refund, sell, take_payment
from apps.payroll import services as payroll
from apps.payroll.models import SalaryRule
from apps.reports.period import earliest
from apps.tasks.models import Task
from tests.test_finance import bank, cash, paid
from tests.test_support import support_client

REPORTS = ["overview", "revenue", "expenses", "money", "members", "attendance", "tasks"]


def url(name):
    return f"/api/reports/{name}/"


def task(w, who, due, status=Task.TODO, title="Restock towels"):
    return Task.objects.create(gym=w.gym, title=title, assignee=who, created_by=w.admin, due_date=due, status=status)


def expense(w, paise, branch=None, category="rent", method="cash", on=None):
    return Expense.objects.create(gym=w.gym, branch=branch or w.a, category=category, method=method, amount_paise=paise, spent_on=on or w.today,
                                  created_by=w.admin, account=Account.objects.for_money((branch or w.a).id, method, on=on or w.today))


def visit(w, day, hour, member=None, staff=None, branch=None):
    at = datetime.combine(day, time(hour), tzinfo=clock.tz(w.gym))
    return CheckIn.objects.create(gym=w.gym, branch=branch or w.a, member=member, staff=staff, at=at, local_date=day, source="desk")


def get(w, name, **params):
    r = w.client(w.admin).get(url(name), params)
    assert r.status_code == 200, r.content
    return r.json()


# ---- the range, roles and isolation, the same for every report ----

@pytest.mark.parametrize("name", REPORTS)
def test_every_report_defaults_to_the_last_7_days_ending_on_the_gyms_today(w, name):
    r = get(w, name)
    assert (r["from"], r["to"], r["days"]) == ((w.today - timedelta(days=6)).isoformat(), w.today.isoformat(), 7)
    if name != "money":  # a balance has no "days before" to compare with
        assert r["previous"] == {"from": (w.today - timedelta(days=13)).isoformat(), "to": (w.today - timedelta(days=7)).isoformat()}


def test_three_calendar_months_is_the_longest_range():
    assert earliest(date(2026, 10, 18)) == date(2026, 7, 19)
    assert earliest(date(2026, 5, 31)) == date(2026, 3, 1)  # 31 Feb doesn't exist: 28 Feb, so from 1 Mar
    assert earliest(date(2026, 11, 30)) == date(2026, 8, 31)
    assert earliest(date(2024, 5, 30)) == date(2024, 3, 1)  # 29 Feb in a leap year, so from 1 Mar


@pytest.mark.parametrize("name", REPORTS)
def test_a_range_over_3_months_or_into_the_future_is_refused(w, name):
    c = w.client(w.admin)
    end = w.today.replace(day=1) - timedelta(days=1)  # last month's last day: month ends are the hard case
    assert c.get(url(name), {"from": earliest(end).isoformat(), "to": end.isoformat()}).status_code == 200
    long = c.get(url(name), {"from": (earliest(end) - timedelta(days=1)).isoformat(), "to": end.isoformat()})
    assert long.status_code == 400 and long.json()["error"]["fields"]["from"] == ["Pick a range of 3 months or less"]
    future = c.get(url(name), {"to": (w.today + timedelta(days=1)).isoformat()})
    assert future.status_code == 400 and future.json()["error"]["fields"]["to"] == ["Pick today or an earlier day"]
    backwards = c.get(url(name), {"from": w.today.isoformat(), "to": (w.today - timedelta(days=1)).isoformat()})
    assert backwards.json()["error"]["fields"]["from"] == ["Pick a start date on or before the end date"]
    assert c.get(url(name), {"from": "yesterday"}).json()["error"]["fields"]["from"]
    assert c.get(url(name), {"branch": "abc"}).status_code == 400


@pytest.mark.parametrize("name", REPORTS)
def test_only_admins_and_support_see_reports(w, other, name):
    for who in (w.desk, w.trainer):
        assert w.client(who).get(url(name)).status_code == 403
    assert w.member_client().get(url(name)).status_code == 403
    stranger = other.client(other.admin)
    stranger.credentials(HTTP_X_GYM=w.gym.slug)
    assert stranger.get(url(name)).status_code == 404
    helper = support_client(w.gym.slug)
    assert helper.get(url(name)).status_code == 404  # no window yet
    from django.utils import timezone

    SupportAccess.objects.create(gym=w.gym, granted_by=w.admin.user, starts=timezone.now(), ends=timezone.now() + timedelta(hours=1))
    assert helper.get(url(name)).status_code == 200


def test_another_gyms_branch_narrows_every_report_to_nothing(w, other):
    cash(w, w.a, opening=5000_00)
    o = {"branch": other.a.id}
    assert get(w, "revenue", **o)["totals"]["revenue_paise"] == 0
    assert get(w, "members", **o)["statuses"]["total"] == 0
    assert get(w, "money", **o)["accounts"] == []
    assert get(w, "overview", **o)["revenue"]["value"] == 0


# ---- each report ----

def test_revenue_is_collected_less_refunds_everywhere_it_shows(w):
    sub = w.member.subscriptions.get()
    refund(sub, amount_paise=50000, method="cash", reason="Moved away", end_plan=False, by=w.admin)
    r = get(w, "revenue")
    assert r["totals"] == {"revenue_paise": 100000, "collected_paise": 150000, "refunds_paise": 50000, "refunds": 1}
    assert r["series"][-1] == {"date": w.today.isoformat(), "revenue_paise": 100000} and len(r["series"]) == 7
    assert r["by_plan"] == [{"key": "Monthly", "label": "Monthly", "paise": 100000}]
    assert {x["key"]: x["paise"] for x in r["by_method"]} == {"upi": 150000, "cash": -50000}
    assert [x["label"] for x in r["by_branch"]] == ["A"]
    assert r["refund_list"][0]["member_name"] == "Asha" and r["refund_list"][0]["amount_paise"] == 50000
    assert r["dues"] == {"members": 0, "total_paise": 0}  # a refund never leaves anyone owing
    assert get(w, "overview")["revenue"] == {"value": 100000, "before": 0}


def test_revenue_by_branch_and_dues_now(w):
    m = w.new_member("Dev", "9811102101", w.b)
    sub = sell(m, w.monthly, by=w.admin)
    take_payment(m, 40000, "cash", by=w.admin, subscription=sub)
    everyone = get(w, "revenue")
    assert {x["label"]: x["paise"] for x in everyone["by_branch"]} == {"A": 150000, "B": 40000}
    assert everyone["dues"] == {"members": 1, "total_paise": 110000}
    b = get(w, "revenue", branch=w.b.id)
    assert b["totals"]["revenue_paise"] == 40000 and b["by_branch"] == [] and b["dues"]["members"] == 1
    assert get(w, "revenue", branch=w.a.id)["dues"]["members"] == 0


def test_expenses_include_bills_and_salaries_and_say_what_is_still_owed(w):
    expense(w, 40000, category="utilities")
    rule = RecurringExpense.objects.create(gym=w.gym, branch=w.a, name="Rent", category="rent", amount_paise=250000, method="bank",
                                           frequency="monthly", starts=w.today, remind_days=3, created_by=w.admin)
    sync_dues(w.gym, w.today)
    pay_due(rule.dues.first(), amount_paise=250000, method="bank", paid_on=w.today, by=w.admin)
    SalaryRule.objects.create(gym=w.gym, staff=w.trainer, branch=w.a, pay_type="fixed", rate_paise=20_000_00, hours_per_day=Decimal(0))
    slip = payroll.generate(w.gym, w.today.replace(day=1))[0]
    payroll.approve(slip, w.admin)
    payroll.pay(slip, amount_paise=5_000_00, method="cash", paid_on=w.today, by=w.admin)
    r = get(w, "expenses")
    assert r["totals"] == {"spent_paise": 40000 + 250000 + 5_000_00, "count": 3}
    assert {x["key"]: x["paise"] for x in r["by_category"]} == {"utilities": 40000, "rent": 250000, "salaries": 5_000_00}
    assert r["by_category"][0]["label"] == "Salaries"  # largest first
    assert r["bills"]["count"] == 1 and r["bills"]["rows"][0]["name"] == "Rent" and r["bills"]["paid_paise"] == 250000
    assert r["salaries"]["people"] == [{"id": w.trainer.id, "name": w.trainer.user.name, "paid_paise": 5_000_00, "payments": 1}]
    assert r["owed"]["salaries"] == 1 and r["owed"]["salaries_paise"] == 15_000_00
    assert r["series"][-1]["spent_paise"] == r["totals"]["spent_paise"]
    assert get(w, "overview")["expenses"]["value"] == r["totals"]["spent_paise"]
    assert get(w, "expenses", branch=w.b.id)["totals"]["spent_paise"] == 0


def test_cash_and_bank_counts_a_shared_account_once_and_shows_it_whole_for_one_branch(w):
    hdfc = bank(w, opening=1_00_000_00, branches=[w.a, w.b])
    till_a, till_b = cash(w, w.a, opening=5000_00), cash(w, w.b, opening=2000_00)
    paid(w, "Ravi", "9811102102", "upi", 150000)                    # A's UPI: into HDFC
    paid(w, "Sita", "9811102103", "upi", 60000, branch=w.b)        # B's UPI: into HDFC too
    paid(w, "Om", "9811102104", "cash", 30000)                     # A's cash
    expense(w, 10000, branch=w.b)                                  # out of B's cash
    money.move(w.gym, kind=MoneyMove.TRANSFER, amount_paise=1000_00, moved_on=w.today, by=w.admin, from_account=till_a, to_account=hdfc)
    r = get(w, "money")
    rows = {a["name"]: a for a in r["accounts"]}
    assert list(rows) == ["A cash", "B cash", "HDFC current"]  # cash first
    assert rows["HDFC current"]["opening_paise"] == 1_00_000_00 and rows["HDFC current"]["in_paise"] == 150000 + 60000 + 1000_00
    assert rows["A cash"]["closing_paise"] == 5000_00 + 30000 - 1000_00 and rows["A cash"]["out_paise"] == 1000_00
    assert r["totals"]["opening_paise"] == 1_00_000_00 + 5000_00 + 2000_00  # HDFC once, though two branches use it
    assert r["totals"]["closing_paise"] == r["totals"]["opening_paise"] + 150000 + 60000 + 30000 - 10000
    assert r["moves"]["count"] == 1 and r["moves"]["rows"][0]["from_name"] == "A cash" and r["moves"]["rows"][0]["to_name"] == "HDFC current"
    # Ending today, a report's closing balance is the account's balance on the money screen.
    live = {a.pk: a.balance_paise for a in money.listed(w.gym)}
    assert all(a["closing_paise"] == live[a["id"]] for a in r["accounts"])
    b = get(w, "money", branch=w.b.id)
    assert [a["name"] for a in b["accounts"]] == ["B cash", "HDFC current"]
    shared = b["accounts"][1]
    assert shared["closing_paise"] == rows["HDFC current"]["closing_paise"] and shared["shared_with"] == ["A"]  # whole, not split
    assert b["moves"]["count"] == 1  # the transfer touched HDFC, which B uses
    assert get(w, "overview")["money"] == {"value": r["totals"]["closing_paise"], "before": r["totals"]["opening_paise"]}
    assert till_b.pk in {a["id"] for a in b["accounts"]}


def test_cash_and_bank_lists_cash_counts_and_the_latest_reconciliation(w):
    hdfc = bank(w, branches=[w.a])
    till = cash(w, w.a, opening=5000_00)
    Account.objects.filter(gym=w.gym).update(opened_on=w.today - timedelta(days=10))  # so a range ending yesterday has them
    money.close_drawer(w.a, counted_paise=4800_00, by=w.desk)
    Reconciliation.objects.create(gym=w.gym, account=hdfc, up_to=w.today - timedelta(days=2), bank_balance_paise=1_00_000_00, by=w.admin)
    Reconciliation.objects.create(gym=w.gym, account=hdfc, up_to=w.today, bank_balance_paise=99_000_00, by=w.admin)
    r = get(w, "money")
    assert r["counts"]["count"] == 1 and r["counts"]["short_paise"] == 200_00 and r["counts"]["to_settle"] == 1
    assert r["counts"]["rows"][0]["difference_paise"] == -200_00 and not r["counts"]["rows"][0]["settled"]
    rec = next(a for a in r["accounts"] if a["id"] == hdfc.id)["reconciled"]
    assert rec["up_to"] == w.today.isoformat() and rec["bank_balance_paise"] == 99_000_00
    earlier = get(w, "money", to=(w.today - timedelta(days=1)).isoformat())
    assert next(a for a in earlier["accounts"] if a["id"] == hdfc.id)["reconciled"]["up_to"] == (w.today - timedelta(days=2)).isoformat()
    assert next(a for a in r["accounts"] if a["id"] == till.id)["reconciled"] is None
    assert get(w, "money", branch=w.b.id)["counts"]["count"] == 0
    DrawerClose.objects.update(settled_at=clock.local(w.gym))
    assert get(w, "money")["counts"]["to_settle"] == 0


def test_members_new_renewed_lapsed_and_statuses_on_the_last_day(w):
    sell(w.member, w.monthly, by=w.desk)  # Asha renews
    w.plan_ending_on(w.today - timedelta(days=2), "Gone", "9811102105")  # ran out two days ago, no new plan
    w.plan_ending_on(w.today, "Today", "9811102106")  # still on today, so not lapsed
    r = get(w, "members")
    assert r["totals"] == {"new": 3, "renewals": 1, "lapsed": 1}
    assert r["statuses"]["total"] == 3 and r["statuses"]["expired"] == 1 and r["statuses"]["expiring"] == 1
    assert sum(d["new"] for d in r["series"]) == 3
    branches = {b["name"]: b for b in r["branches"]}
    assert branches["A"]["new"] == 3 and branches["A"]["renewals"] == 1 and branches["A"]["active"] == 2 and branches["B"]["new"] == 0
    assert get(w, "members", branch=w.b.id)["branches"] == []
    assert get(w, "overview")["members"]["value"] == 3


def test_attendance_by_day_session_and_branch_members_and_staff_apart(w):
    yesterday = w.today - timedelta(days=1)
    visit(w, w.today, 6, member=w.member)
    visit(w, yesterday, 18, member=w.member)
    visit(w, w.today, 17, staff=w.trainer)
    visit(w, w.today, 7, staff=w.desk_b, branch=w.b)
    r = get(w, "attendance")
    assert r["totals"] == {"member": 2, "trainer": 1, "receptionist": 1, "admin": 0}
    assert r["series"][-1] == {"date": w.today.isoformat(), "member": 1, "staff": 2} and r["series"][-2]["member"] == 1
    assert [s["session"] for s in r["sessions"]] == ["Morning", "Evening"]
    assert r["sessions"][0]["member"] == 1 and r["sessions"][0]["receptionist"] == 1 and r["sessions"][1]["trainer"] == 1
    assert {b["name"]: (b["member"], b["staff"]) for b in r["branches"]} == {"A": (2, 1), "B": (0, 1)}
    assert get(w, "attendance", branch=w.b.id)["totals"]["member"] == 0
    assert get(w, "overview")["attendance"]["value"] == 2


def test_tasks_due_in_the_days_by_person_with_the_oldest_overdue(w):
    yesterday = w.today - timedelta(days=1)
    task(w, w.trainer, yesterday, Task.DONE, "Call lapsed members")
    late = task(w, w.trainer, yesterday, Task.DOING, "Fix the leg press")
    task(w, w.desk_b, w.today + timedelta(days=1), title="Too late for this period")
    task(w, w.desk_b, w.today - timedelta(days=2), title="Count the towels")
    r = get(w, "tasks")
    assert r["totals"] == {"total": 3, "done": 1, "doing": 1, "todo": 1, "overdue": 2}
    assert r["people"][0]["name"] == w.trainer.user.name and (r["people"][0]["total"], r["people"][0]["done"]) == (2, 1)
    assert [x["title"] for x in r["late"]] == ["Count the towels", "Fix the leg press"] and r["late"][1]["id"] == late.id
    assert get(w, "tasks", branch=w.b.id)["totals"]["total"] == 1
    assert get(w, "overview")["tasks"] == {"value": 1, "before": 0, "total": 3}


def test_trends_compare_the_same_number_of_days_just_before(w):
    expense(w, 30000, on=w.today - timedelta(days=8))
    expense(w, 45000)
    assert get(w, "expenses")["before"] == {"spent_paise": 30000}
    assert get(w, "overview")["expenses"] == {"value": 45000, "before": 30000}


# ---- query budgets: flat however many rows ----

def _queries(w, name):
    c = w.client(w.admin)
    with CaptureQueriesContext(connection) as ctx:
        assert c.get(url(name), {"from": (w.today - timedelta(days=60)).isoformat()}).status_code == 200
    return len(ctx)


def _more_rows(w, n, offset):
    hdfc = Account.objects.filter(gym=w.gym, kind="bank").first()
    for i in range(n):
        k = offset + i
        m = w.new_member(f"New {k}", f"97000{5000 + k:05d}", w.a if k % 2 else w.b)
        sub = sell(m, w.monthly, by=w.admin)
        take_payment(m, 50000, "upi" if k % 2 else "cash", by=w.admin, subscription=sub)
        if k % 3 == 0:
            refund(sub, amount_paise=10000, method="cash", reason="Goodwill", end_plan=False, by=w.admin)
        expense(w, 1000 + k, branch=w.a if k % 2 else w.b, category=["rent", "supplies", "other"][k % 3], on=w.today - timedelta(days=k % 20))
        task(w, w.trainer if k % 2 else w.desk_b, w.today - timedelta(days=k % 5), title=f"Task {k}")
        visit(w, w.today - timedelta(days=k % 30), 6 + k % 14, member=m)
        money.move(w.gym, kind=MoneyMove.DEPOSIT, amount_paise=100_00, moved_on=w.today - timedelta(days=k % 10), by=w.admin, to_account=hdfc)
        Reconciliation.objects.create(gym=w.gym, account=hdfc, up_to=w.today - timedelta(days=k), bank_balance_paise=0, by=w.admin)


@pytest.mark.parametrize("name, budget", [
    ("overview", 10), ("revenue", 15), ("expenses", 13), ("money", 8), ("members", 11), ("attendance", 10), ("tasks", 6),
])
def test_each_report_runs_a_fixed_number_of_queries(w, name, budget):
    bank(w, branches=[w.a, w.b])
    cash(w, w.a)
    cash(w, w.b)
    Account.objects.filter(gym=w.gym).update(opened_on=w.today - timedelta(days=60))  # money moves can be dated back to then
    _more_rows(w, 3, 0)
    few = _queries(w, name)
    _more_rows(w, 9, 3)
    assert _queries(w, name) == few <= budget
