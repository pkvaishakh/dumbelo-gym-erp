from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from apps.attendance.models import CheckIn
from apps.audit.models import AuditLog
from apps.core import clock
from apps.expenses.models import Expense
from apps.payroll import services
from apps.payroll.models import Payslip, SalaryItem, SalaryRule

RULES = "/api/salary-rules/"
SLIPS = "/api/payslips/"


def month_of(w):
    return w.today.replace(day=1)


def mkey(w):
    return month_of(w).strftime("%Y-%m")


def checked_in(w, staff, days):
    """`staff` checked in on each of the first `days` days of this month (as far as today)."""
    m = month_of(w)
    for i in range(days):
        d = m + timedelta(days=i)
        CheckIn.objects.create(gym=w.gym, branch=w.a, staff=staff, at=datetime.combine(d, datetime.min.time(), tzinfo=clock.tz(w.gym)) + timedelta(hours=9),
                               local_date=d, source="desk")


def salary(w, staff, pay_type="fixed", rate=20_000_00, hours=0, items=()):
    rule = SalaryRule.objects.create(gym=w.gym, staff=staff, branch=w.a, pay_type=pay_type, rate_paise=rate, hours_per_day=Decimal(hours))
    for kind, label, paise in items:
        SalaryItem.objects.create(rule=rule, kind=kind, label=label, amount_paise=paise)
    return rule


def generate(w):
    r = w.client(w.admin).post(f"{SLIPS}generate/", {"month": mkey(w)}, format="json")
    assert r.status_code == 200, r.json()
    return {s["staff"]: s for s in r.json()}


def test_working_days_leave_out_the_weekly_day_off():
    assert services.working_days(date(2026, 10, 1), "Sunday") == 27  # Sundays fall on 4, 11, 18 and 25 Oct
    assert services.working_days(date(2026, 10, 1), "") == 31
    assert services.working_days(date(2026, 2, 1), "Monday") == 24


@pytest.mark.parametrize("pay_type,rate,hours,present,working,expected", [
    ("fixed", 20_000_00, 0, 3, 26, 20_000_00),
    ("attendance", 26_000_00, 0, 13, 26, 13_000_00),
    ("attendance", 26_000_00, 0, 30, 26, 26_000_00),  # never more than the salary
    ("attendance", 10_000_00, 0, 1, 3, 3_333_00),  # ₹3,333.33 rounds to the rupee
    ("attendance", 10_000_00, 0, 2, 3, 6_667_00),  # ₹6,666.67 too
    ("attendance", 10_000_00, 0, 5, 0, 0),
    ("daily", 800_00, 0, 22, 26, 17_600_00),
    ("hourly", 150_50, Decimal("6.5"), 20, 26, 19_565_00),
    ("hourly", 150_50, Decimal("6.25"), 1, 26, 941_00),  # ₹940.625 rounds up
])
def test_pay_for_each_pay_type(pay_type, rate, hours, present, working, expected):
    assert services.pay_for(pay_type, rate, Decimal(hours), present, working) == expected


def test_admin_sets_a_salary(w, other):
    c = w.client(w.admin)
    body = {"staff": w.trainer.id, "branch": w.a.id, "pay_type": "attendance", "rate_paise": 26_000_00,
            "items": [{"kind": "allowance", "label": "Travel", "amount_paise": 1_000_00}, {"kind": "deduction", "label": "PF", "amount_paise": 1_800_00}]}
    r = c.post(RULES, body, format="json")
    assert r.status_code == 201, r.json()
    assert r.json()["staff_name"] == "Trainer0" and len(r.json()["items"]) == 2
    assert c.post(RULES, body, format="json").status_code == 400  # one each
    rid = r.json()["id"]
    r = c.patch(f"{RULES}{rid}/", {"items": [{"kind": "allowance", "label": "Phone", "amount_paise": 500_00}]}, format="json")
    assert [i["label"] for i in r.json()["items"]] == ["Phone"]
    assert c.get(RULES, {"staff": w.trainer.id}).json()[0]["id"] == rid
    assert AuditLog.objects.filter(action="salary.changed", object_id=str(rid)).exists()
    # Hourly needs the shift's hours; another gym's people and members are refused.
    assert c.post(RULES, {**body, "staff": w.desk.id, "pay_type": "hourly", "items": []}, format="json").json()["error"]["fields"]["hours_per_day"]
    assert c.post(RULES, {**body, "staff": other.trainer.id}, format="json").status_code == 400
    member_role = w.member_client() and w.member.user.gym_roles.get(gym=w.gym)
    assert c.post(RULES, {**body, "staff": member_role.id}, format="json").status_code == 400


def test_generate_works_out_each_pay_type_from_check_ins(w):
    w.trainer.day_off = "Sunday"
    w.trainer.save()
    salary(w, w.trainer, "attendance", 27_000_00, items=[("allowance", "Travel", 1_000_00), ("deduction", "PF", 500_00)])
    salary(w, w.desk, "daily", 700_00)
    salary(w, w.desk_b, "hourly", 100_00, hours=6)
    salary(w, w.admin, "fixed", 50_000_00)
    present = min(w.today.day, 5)
    for s in (w.trainer, w.desk, w.desk_b):
        checked_in(w, s, present)
    slips = generate(w)
    t = slips[w.trainer.id]
    working = services.working_days(month_of(w), "Sunday")
    assert t["working_days"] == working and t["days_present"] == present and t["status"] == "draft"
    assert t["pay_paise"] == services.pay_for("attendance", 27_000_00, Decimal(0), present, working)
    assert t["additions_paise"] == 1_000_00 and t["deductions_paise"] == 500_00 and t["net_paise"] == t["pay_paise"] + 500_00
    assert slips[w.desk.id]["net_paise"] == 700_00 * present
    assert slips[w.desk_b.id]["net_paise"] == 600_00 * present
    assert slips[w.admin.id]["net_paise"] == 50_000_00 and slips[w.admin.id]["payment_status"] == "unpaid"
    # Running it again changes nothing and adds nothing.
    assert generate(w) == slips and Payslip.objects.count() == 4


def test_drafts_follow_the_rule_and_approved_ones_stay(w):
    rule = salary(w, w.trainer, "fixed", 20_000_00)
    salary(w, w.desk, "fixed", 15_000_00)
    slips = generate(w)
    c = w.client(w.admin)
    c.post(f"{SLIPS}{slips[w.desk.id]['id']}/approve/")
    rule.rate_paise = 22_000_00
    rule.save()
    SalaryRule.objects.filter(staff=w.desk).update(rate_paise=99_000_00)
    again = generate(w)
    assert again[w.trainer.id]["net_paise"] == 22_000_00
    assert again[w.desk.id]["net_paise"] == 15_000_00 and again[w.desk.id]["status"] == "approved"


def test_lines_days_and_approval(w):
    salary(w, w.trainer, "daily", 1_000_00)
    checked_in(w, w.trainer, 1)
    slip = generate(w)[w.trainer.id]
    c = w.client(w.admin)
    url = f"{SLIPS}{slip['id']}/"
    r = c.post(url + "days/", {"days_present": 20}, format="json").json()
    assert r["days_present"] == 20 and r["days_set_by_hand"] is True and r["net_paise"] == 20_000_00
    r = c.post(url + "lines/", {"kind": "incentive", "label": "PT sessions", "amount_paise": 3_000_00}, format="json").json()
    r = c.post(url + "lines/", {"kind": "referral", "label": "2 members joined", "amount_paise": 1_000_00}, format="json").json()
    r = c.post(url + "lines/", {"kind": "deduction", "label": "Advance", "amount_paise": 5_000_00}, format="json").json()
    assert (r["additions_paise"], r["deductions_paise"], r["net_paise"]) == (4_000_00, 5_000_00, 19_000_00)
    too_much = c.post(url + "lines/", {"kind": "deduction", "label": "Fine", "amount_paise": 50_000_00}, format="json")
    assert too_much.json()["error"]["code"] == "deductions_too_high"
    advance = next(x for x in r["lines"] if x["label"] == "Advance")
    assert c.post(url + "remove-line/", {"line": advance["id"]}, format="json").json()["net_paise"] == 24_000_00
    # Days set by hand survive working payroll out again.
    assert generate(w)[w.trainer.id]["days_present"] == 20
    r = c.post(url + "approve/").json()
    assert r["status"] == "approved" and r["approved_by_name"] == "Admin0"
    assert c.post(url + "days/", {"days_present": 3}, format="json").json()["error"]["code"] == "approved"
    assert c.post(url + "approve/").status_code == 409
    for action in ("payslip.days_set", "payslip.line_added", "payslip.line_removed", "payslip.approved"):
        assert AuditLog.objects.filter(action=action, object_id=str(slip["id"])).exists(), action


def test_pay_in_parts_after_approval(w):
    salary(w, w.trainer, "fixed", 20_000_00)
    slip = generate(w)[w.trainer.id]
    c = w.client(w.admin)
    url = f"{SLIPS}{slip['id']}/"
    assert c.post(url + "pay/", {"amount_paise": 100, "method": "bank"}, format="json").json()["error"]["code"] == "not_approved"
    c.post(url + "approve/")
    r = c.post(url + "pay/", {"amount_paise": 5_000_00, "method": "cash"}, format="json").json()
    assert (r["paid_paise"], r["owed_paise"], r["payment_status"]) == (5_000_00, 15_000_00, "part")
    over = c.post(url + "pay/", {"amount_paise": 15_000_01, "method": "bank"}, format="json").json()["error"]
    assert over["code"] == "overpaid" and "₹15,000" in over["message"]
    r = c.post(url + "pay/", {"amount_paise": 15_000_00, "method": "bank", "note": "October"}, format="json").json()
    assert r["payment_status"] == "paid" and len(r["payments"]) == 2 and r["payments"][0]["paid_by_name"] == "Admin0"
    assert c.post(url + "pay/", {"amount_paise": 1, "method": "bank"}, format="json").json()["error"]["code"] == "nothing_due"
    spent = Expense.objects.filter(salary_payment__payslip_id=slip["id"])
    assert spent.count() == 2 and {e.category for e in spent} == {"salaries"} and {e.paid_to for e in spent} == {"Trainer0"}
    e = spent.first()
    assert c.patch(f"/api/expenses/{e.id}/", {"amount_paise": 1}, format="json").json()["error"]["code"] == "paid_a_salary"
    # Reopened, it can't drop below what is paid.
    c.post(url + "reopen/")
    assert c.post(url + "lines/", {"kind": "deduction", "label": "Fine", "amount_paise": 100}, format="json").json()["error"]["code"] == "below_paid"


def test_fixed_deductions_never_stop_payroll(w):
    """A few days present can earn less than the month's PF: the net stops at zero and the others still work out."""
    salary(w, w.trainer, "attendance", 26_000_00, items=[("deduction", "PF", 1_800_00)])
    salary(w, w.desk, "fixed", 15_000_00)
    slips = generate(w)
    assert slips[w.trainer.id]["net_paise"] == 0 and slips[w.trainer.id]["deductions_paise"] == 1_800_00
    assert slips[w.desk.id]["net_paise"] == 15_000_00


def test_an_approved_payslip_with_nothing_to_pay_is_settled(w):
    salary(w, w.trainer, "attendance", 26_000_00, items=[("deduction", "PF", 1_800_00)])
    slip = generate(w)[w.trainer.id]
    r = w.client(w.admin).post(f"{SLIPS}{slip['id']}/approve/").json()
    assert (r["net_paise"], r["payment_status"]) == (0, "paid")


def test_daily_wages_are_paid_as_the_days_go(w):
    salary(w, w.desk, "daily", 800_00)
    checked_in(w, w.desk, 1)
    slip = generate(w)[w.desk.id]
    r = w.client(w.admin).post(f"{SLIPS}{slip['id']}/pay/", {"amount_paise": 800_00, "method": "cash"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "draft" and r.json()["payment_status"] == "paid"


def test_home_and_summary_count_unpaid_approved_salaries(w):
    salary(w, w.trainer, "fixed", 20_000_00)
    salary(w, w.desk, "fixed", 15_000_00)
    slips = generate(w)
    c = w.client(w.admin)
    c.post(f"{SLIPS}{slips[w.trainer.id]['id']}/approve/")
    c.post(f"{SLIPS}{slips[w.trainer.id]['id']}/pay/", {"amount_paise": 5_000_00, "method": "cash"}, format="json")
    dues = c.get("/api/reports/summary/").json()["expense_dues"]
    assert (dues["salaries"], dues["total_paise"]) == (1, 15_000_00)
    owed = c.get(SLIPS, {"owed": "true"}).json()["results"]
    assert [(o["staff"], o["owed_paise"]) for o in owed] == [(w.trainer.id, 15_000_00)]
    s = c.get(f"{SLIPS}summary/", {"month": mkey(w)}).json()
    assert (s["payslips"], s["drafts"], s["approved"], s["net_paise"], s["paid_paise"]) == (2, 1, 1, 35_000_00, 5_000_00)
    assert s["staff_without_salary"] == 2  # the admin and the second receptionist


def test_months_still_to_come_are_refused(w):
    nxt = clock.add_months(month_of(w), 1).strftime("%Y-%m")
    r = w.client(w.admin).post(f"{SLIPS}generate/", {"month": nxt}, format="json")
    assert r.json()["error"]["code"] == "future_month"
    assert w.client(w.admin).post(f"{SLIPS}generate/", {"month": "2026-13"}, format="json").status_code == 400
    assert w.client(w.admin).get(SLIPS, {"month": "Oct"}).status_code == 400


def test_only_admins_and_only_this_gym(w, other):
    salary(w, w.trainer)
    slip = generate(w)[w.trainer.id]
    for role in (w.desk, w.trainer):
        c = w.client(role)
        assert c.get(SLIPS).status_code == 403 and c.get(RULES).status_code == 403
        assert c.post(f"{SLIPS}{slip['id']}/approve/").status_code == 403
    them = other.client(other.admin)
    assert them.get(f"{SLIPS}{slip['id']}/").status_code == 404
    assert them.post(f"{SLIPS}{slip['id']}/pay/", {"amount_paise": 1, "method": "cash"}, format="json").status_code == 404
    assert them.get(SLIPS).json()["results"] == []


def test_salary_history_and_list_budget(w, django_assert_max_num_queries):
    for s in (w.trainer, w.desk, w.desk_b, w.admin):
        salary(w, s)
    generate(w)
    c = w.client(w.admin)
    with django_assert_max_num_queries(8):
        assert len(c.get(SLIPS, {"month": mkey(w)}).json()["results"]) == 4
    with django_assert_max_num_queries(8):
        assert len(c.get(RULES).json()) == 4
    history = c.get(SLIPS, {"staff": w.trainer.id}).json()["results"]
    assert [h["month"] for h in history] == [month_of(w).isoformat()]
