from datetime import timedelta

from apps.audit.models import AuditLog
from apps.members.models import Offer, Payment


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
