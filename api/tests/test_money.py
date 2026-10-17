from datetime import timedelta

from apps.audit.models import AuditLog
from apps.expenses.models import Expense
from apps.members.models import Offer, Payment
from apps.members.services import sell, take_payment


def test_new_member_with_plan_offer_and_payment(w):
    offer = Offer.objects.create(gym=w.gym, name="Diwali", percent_off=10, starts=w.today, ends=w.today + timedelta(days=5))
    r = w.client(w.desk).post("/api/members/", {
        "name": "Ravi", "phone": "9833333333", "home_branch": w.a.id, "first_plan": w.monthly.id, "offer": offer.id,
        "paid_paise": 100000, "method": "cash", "password": "secret1",
    }, format="json")
    assert r.status_code == 201, r.json()
    m = r.json()
    assert m["code"].endswith("-1001") and m["has_login"] is True
    assert m["balance_paise"] == 135000 - 100000 and m["status"] == "due"


def test_offer_must_apply(w):
    old = Offer.objects.create(gym=w.gym, name="Old", amount_off_paise=5000, starts=w.today - timedelta(days=30), ends=w.today - timedelta(days=1))
    r = w.client(w.desk).post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id, "offer": old.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "offer_not_valid"


def test_renewal_starts_after_current_plan(w):
    cur = w.member.current_subscription()
    r = w.client(w.desk).post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id}, format="json")
    assert r.json()["starts"] == str(cur.ends + timedelta(days=1))


def test_cannot_overpay_and_collection(w):
    c = w.client(w.desk)
    r = c.post("/api/payments/", {"member": w.member.id, "amount_paise": 100, "method": "cash"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "nothing_due"
    col = c.get("/api/payments/collection/").json()
    assert col["total_paise"] == 150000 and col["by_method"]["upi"] == 150000



def test_collection_filters_match_the_list(w):
    ravi = w.new_member("Ravi", "9844444444", w.b)
    sell(ravi, w.monthly, by=w.admin)
    take_payment(ravi, 50000, "cash", by=w.admin, branch=w.b)
    old = take_payment(ravi, 20000, "card", by=w.admin, branch=w.b)
    old.taken_at -= timedelta(days=10)
    old.save(update_fields=["taken_at"])
    c = w.client(w.admin)
    week = {"from": str(w.today - timedelta(days=6)), "to": str(w.today)}
    col = c.get("/api/payments/collection/", week).json()
    assert col["total_paise"] == 200000 and col["count"] == 2 and col["from"] == week["from"]
    month = {"from": str(w.today - timedelta(days=30)), "to": str(w.today)}
    assert c.get("/api/payments/collection/", month).json()["by_method"]["card"] == 20000
    narrowed = {**month, "q": "ravi", "method": "cash", "branch": w.b.id}
    assert c.get("/api/payments/collection/", narrowed).json()["total_paise"] == 50000
    assert [p["amount_paise"] for p in c.get("/api/payments/", narrowed).json()["results"]] == [50000]
    assert c.get("/api/payments/", {"q": w.member.phone[-6:]}).json()["count"] == 1
    backwards = c.get("/api/payments/collection/", {"from": week["to"], "to": week["from"]})
    assert backwards.status_code == 400 and "from" in backwards.json()["error"]["fields"]


def test_receptionist_sees_one_day_at_a_time(w):
    c = w.client(w.desk)
    today = str(w.today)
    assert c.get("/api/payments/collection/", {"from": today, "to": today}).json()["total_paise"] == 150000
    week = {"from": str(w.today - timedelta(days=6)), "to": today}
    for url in ("/api/payments/collection/", "/api/payments/"):
        r = c.get(url, week)
        assert r.status_code == 409 and r.json()["error"]["code"] == "not_allowed"

def test_only_admin_corrects_or_voids_and_it_is_audited(w):
    p = Payment.objects.get()
    assert w.client(w.desk).post(f"/api/payments/{p.id}/void/", {"reason": "x"}, format="json").status_code == 403
    c = w.client(w.admin)
    assert c.patch(f"/api/payments/{p.id}/", {"method": "cash", "reason": "Paid cash, typed UPI"}, format="json").status_code == 200
    assert c.post(f"/api/payments/{p.id}/void/", {"reason": "Duplicate"}, format="json").status_code == 200
    assert list(AuditLog.objects.values_list("action", flat=True).order_by("at")) == ["payment.corrected", "payment.voided"]
    w.member.refresh_from_db()
    assert w.member.balance_paise() == 150000


def test_freeze_moves_end_date(w):
    sub = w.member.current_subscription()
    ends = sub.ends
    r = w.client(w.desk).post(f"/api/subscriptions/{sub.id}/freeze/", {"until": str(w.today + timedelta(days=9))}, format="json")
    assert r.status_code == 200 and r.json()["ends"] == str(ends + timedelta(days=10))
    assert w.client(w.desk).get(f"/api/members/{w.member.id}/").json()["status"] == "frozen"


def test_summary(w):
    s = w.client(w.admin).get("/api/reports/summary/").json()
    assert s["members"]["active"] == 1 and s["revenue"]["today_paise"] == 150000
    assert w.client(w.desk).get("/api/reports/summary/").status_code == 403


def test_summary_splits_the_day_by_branch(w):
    Expense.objects.create(gym=w.gym, branch=w.b, category="rent", method="cash", amount_paise=40000, spent_on=w.today, created_by=w.admin)
    s = w.client(w.admin).get("/api/reports/summary/").json()
    assert s["expenses_today_paise"] == 40000
    by = {b["name"]: b for b in s["branches"]}
    assert by["A"]["revenue_today_paise"] == 150000 and by["A"]["active_members"] == 1 and by["A"]["expenses_today_paise"] == 0
    assert by["B"]["expenses_today_paise"] == 40000 and by["B"]["revenue_today_paise"] == 0
    one = w.client(w.admin).get(f"/api/reports/summary/?branch={w.b.id}").json()
    assert one["expenses_today_paise"] == 40000 and "branches" not in one


def test_profile_pages_plans_and_payments_newest_first(w):
    """The member profile asks for a few plans and payments at a time, never the whole history."""
    for _ in range(3):
        sub = sell(w.member, w.monthly, by=w.desk)
        take_payment(w.member, sub.price_paise, "cash", by=w.desk)
    c = w.client(w.desk)
    subs = c.get(f"/api/subscriptions/?member={w.member.id}&limit=2").json()
    assert subs["count"] == 4 and len(subs["results"]) == 2 and subs["next"]
    starts = [s["starts"] for s in subs["results"] + c.get(subs["next"]).json()["results"]]
    assert starts == sorted(starts, reverse=True)
    pays = c.get(f"/api/payments/?member={w.member.id}&limit=2").json()
    assert pays["count"] == 4 and len(pays["results"]) == 2 and pays["next"]


def test_profile_plan_says_when_it_is_frozen(w):
    sub = w.member.current_subscription()
    until = w.today + timedelta(days=9)
    w.client(w.desk).post(f"/api/subscriptions/{sub.id}/freeze/", {"until": str(until)}, format="json")
    plan = w.client(w.desk).get(f"/api/members/{w.member.id}/").json()["plan"]
    assert plan["id"] == sub.id and plan["frozen_from"] == str(w.today) and plan["frozen_until"] == str(until)
