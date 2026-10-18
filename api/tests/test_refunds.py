"""Refunds: money given back for a plan, out of an account, never more than was paid, and less revenue in reports."""
from datetime import timedelta

from apps.audit.models import AuditLog
from apps.finance import services as money
from apps.members.models import Member, Refund
from apps.members.services import sell, take_payment
from tests.test_finance import ACCOUNTS, bank, cash

REFUNDS = "/api/refunds/"


def give(c, sub, paise, method="cash", end_plan=False, reason="Moving cities"):
    return c.post(REFUNDS, {"subscription": sub.id, "amount_paise": paise, "method": method, "reason": reason, "end_plan": end_plan}, format="json")


def member(w, name="Ravi", phone="9811111111", pay=1_500_00, method="cash"):
    m = w.new_member(name, phone, w.a)
    sub = sell(m, w.monthly, by=w.desk, starts=w.today - timedelta(days=5))
    if pay:
        take_payment(m, pay, method, by=w.desk)
    return m, sub


def owed(m):
    return Member.objects.with_totals().get(pk=m.pk).balance_paise()


def test_a_refund_comes_out_of_the_drawer_and_never_makes_anyone_owe(w):
    drawer = cash(w, w.a, opening=500_00)
    m, sub = member(w)
    c = w.client(w.admin)
    r = give(c, sub, 500_00)
    assert r.status_code == 201, r.json()
    body = r.json()
    assert (body["amount_paise"], body["plan_name"], body["ended_plan"], body["refunded_by_name"]) == (500_00, "Monthly", False, w.admin.user.name)
    assert owed(m) == 0 and m.balance_paise() == 0 and Member.objects.with_totals().get(pk=m.pk).status(w.today) == "active"
    assert money.balance_of(drawer) == 1_500_00  # 500 + 1,500 taken - 500 given back
    s = c.get(f"/api/subscriptions/{sub.id}/").json()
    assert (s["paid_paise"], s["refunded_paise"], s["ends"]) == (1_500_00, 500_00, sub.ends.isoformat())
    assert [(e["kind"], e["amount_paise"]) for e in c.get(f"{ACCOUNTS}{drawer.id}/statement/").json()["entries"]][-1] == ("refund", -500_00)
    log = AuditLog.objects.get(action="refund.given")
    assert (log.after["amount_paise"], log.after["reason"]) == (500_00, "Moving cities")


def test_never_more_than_was_paid_for_the_plan(w):
    m, sub = member(w, pay=1_000_00)
    c = w.client(w.admin)
    r = give(c, sub, 1_000_01)
    assert (r.status_code, r.json()["error"]["code"]) == (409, "more_than_paid")
    assert r.json()["error"]["message"] == "₹1,000 was paid for this plan and isn't refunded yet. Refund that or less."
    give(c, sub, 400_00)
    assert owed(m) == 500_00  # it still owes what it owed: the refund lowered the price as much as the paid
    assert give(c, sub, 600_01).json()["error"]["code"] == "more_than_paid"
    give(c, sub, 600_00)
    assert give(c, sub, 1).json()["error"]["code"] == "nothing_paid"
    assert give(c, sub, 0).status_code == 400


def test_ending_the_plan_today_and_voiding_puts_it_back(w):
    drawer = cash(w, w.a)
    m, sub = member(w)
    was = sub.ends
    c = w.client(w.admin)
    r = give(c, sub, 1_000_00, end_plan=True).json()
    sub.refresh_from_db()
    assert r["ended_plan"] and sub.ends == w.today and Member.objects.with_totals().get(pk=m.pk).status(w.today) == "expiring"
    assert owed(m) == 0
    v = c.post(f"{REFUNDS}{r['id']}/void/", {"reason": "Changed their mind"}, format="json")
    assert v.status_code == 200 and v.json()["voided"]
    sub.refresh_from_db()
    assert sub.ends == was
    assert money.balance_of(drawer) == 1_500_00 and owed(m) == 0
    assert c.post(f"{REFUNDS}{r['id']}/void/", {"reason": "Again"}, format="json").json()["error"]["code"] == "voided"
    assert AuditLog.objects.filter(action="refund.voided", object_id=str(r["id"])).exists()


def test_a_plan_that_hasnt_started_is_cancelled_when_all_of_it_is_refunded(w):
    m, sub = member(w)
    renewal = sell(m, w.monthly, by=w.desk)  # starts when the current one ends
    take_payment(m, 1_500_00, "cash", by=w.desk)
    c = w.client(w.admin)
    r = give(c, renewal, 1_000_00, end_plan=True)
    assert (r.status_code, r.json()["error"]["code"]) == (409, "not_started")
    r = give(c, renewal, 1_500_00, end_plan=True).json()
    renewal.refresh_from_db()
    assert r["cancelled_plan"] and renewal.cancelled
    assert owed(m) == 0 and m.balance_paise() == 0  # no credit left over from the cancelled plan's payment
    assert give(c, renewal, 1).json()["error"]["code"] == "cancelled"
    c.post(f"{REFUNDS}{r['id']}/void/", {"reason": "Wrong plan"}, format="json")
    renewal.refresh_from_db()
    assert not renewal.cancelled and owed(m) == 0


def test_a_refunded_plan_can_be_cancelled(w):
    m, sub = member(w, pay=0)
    take_payment(m, 1_500_00, "cash", by=w.desk)
    c = w.client(w.admin)
    assert c.post(f"/api/subscriptions/{sub.id}/cancel/", {"reason": "x"}, format="json").json()["error"]["code"] == "has_payments"
    give(c, sub, 1_500_00)
    assert c.post(f"/api/subscriptions/{sub.id}/cancel/", {"reason": "Left"}, format="json").status_code == 200
    assert owed(m) == 0


def test_reports_count_refunds_as_less_revenue(w):
    _, sub = member(w, pay=1_500_00, method="upi")
    c = w.client(w.admin)
    before = c.get("/api/reports/summary/").json()["revenue"]["today_paise"]
    give(c, sub, 500_00, method="upi")
    assert c.get("/api/reports/summary/").json()["revenue"]["today_paise"] == before - 500_00
    p = c.get("/api/reports/period/").json()
    assert p["totals"]["refunds_paise"] == 500_00
    assert p["series"][-1]["revenue_paise"] == before - 500_00
    assert {r["name"]: r["paise"] for r in p["revenue_by_plan"]}["Monthly"] == before - 500_00


def test_only_admins_give_refunds_and_the_desk_sees_its_own_branches(w):
    _, sub = member(w)
    r = give(w.client(w.admin), sub, 100_00).json()
    desk = w.client(w.desk)
    assert give(desk, sub, 100_00).status_code == 403
    assert desk.post(f"{REFUNDS}{r['id']}/void/", {"reason": "x"}, format="json").status_code == 403
    assert [x["id"] for x in desk.get(REFUNDS, {"member": sub.member_id}).json()["results"]] == [r["id"]]
    assert w.client(w.desk_b).get(REFUNDS).json()["results"] == []
    assert w.client(w.desk_b).get(f"{REFUNDS}{r['id']}/").status_code == 404
    assert w.client(w.trainer).get(REFUNDS).status_code == 403
    assert w.member_client().get(REFUNDS).status_code == 403


def test_another_gyms_plans_and_refunds_stay_out_of_reach(w, other):
    m = other.new_member("Zed", "9899999999", other.a)
    theirs = sell(m, other.monthly, by=other.desk)
    take_payment(m, 1_500_00, "cash", by=other.desk)
    r = give(other.client(other.admin), theirs, 100_00).json()
    c = w.client(w.admin)
    assert give(c, theirs, 100_00).status_code == 400
    assert c.get(f"{REFUNDS}{r['id']}/").status_code == 404
    assert c.post(f"{REFUNDS}{r['id']}/void/", {"reason": "x"}, format="json").status_code == 404


def test_a_reconciled_refund_cant_be_voided(w):
    hdfc = bank(w, branches=[w.a], opening=0)
    _, sub = member(w, method="upi")
    c = w.client(w.admin)
    r = give(c, sub, 500_00, method="upi").json()
    pay = sub.payments.get()
    c.post(f"{ACCOUNTS}{hdfc.id}/tick/", {"entries": [{"kind": "payment", "id": pay.id}, {"kind": "refund", "id": r["id"]}], "ticked": True}, format="json")
    assert c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": w.today.isoformat(), "bank_balance_paise": 1_000_00}, format="json").status_code == 200
    v = c.post(f"{REFUNDS}{r['id']}/void/", {"reason": "x"}, format="json")
    assert (v.status_code, v.json()["error"]["code"]) == (409, "reconciled")


def test_refunds_list_within_a_query_budget(w, django_assert_max_num_queries):
    c = w.client(w.admin)

    def grow(n):
        for i in range(n):
            _, sub = member(w, f"R{i}", f"98333{Refund.objects.count() + 5000:05d}")
            give(c, sub, 100_00)
    grow(2)
    with django_assert_max_num_queries(10) as q:
        assert c.get(REFUNDS).status_code == 200
    few = len(q.captured_queries)
    grow(6)
    with django_assert_max_num_queries(few):
        assert c.get(REFUNDS).status_code == 200
