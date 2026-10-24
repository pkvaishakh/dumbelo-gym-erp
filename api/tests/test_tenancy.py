from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.gyms.models import SupportAccess


def test_login_and_me(w, client):
    r = client.post("/api/auth/login/", {"username": "Admin0", "password": "pass12345"}, content_type="application/json")
    assert r.status_code == 200
    me = client.get("/api/me/", HTTP_AUTHORIZATION="Bearer " + r.json()["access"]).json()
    assert me["roles"][0]["gym"] == "iron" and me["roles"][0]["role"] == "admin"
    assert {b["name"] for b in me["roles"][0]["branches"]} == {"A", "B"}


def test_wrong_password(w, client):
    r = client.post("/api/auth/login/", {"username": "admin0", "password": "nope"}, content_type="application/json")
    assert r.status_code == 401 and r.json()["error"]["code"] == "login_failed"


def test_needs_gym_header(w):
    c = w.client(w.admin)
    c.credentials()
    assert c.get("/api/members/").status_code in (400, 401)


def test_other_gym_is_invisible(w, other):
    c = w.client(w.admin)
    c.credentials(HTTP_X_GYM="steel")
    assert c.get("/api/members/").status_code == 404
    # and ids from another gym don't resolve inside your own
    assert w.client(w.admin).get(f"/api/members/{other.member.id}/").status_code == 404


def test_receptionist_sees_only_their_branch(w):
    w.new_member("Bina", "9811111111", w.b)
    names = [m["name"] for m in w.client(w.desk).get("/api/members/").json()["results"]]
    assert names == ["Asha"]
    assert len(w.client(w.admin).get("/api/members/").json()["results"]) == 2


def test_desk_cant_sell_or_take_money_for_another_branchs_member(w):
    bina = w.new_member("Bina", "9811111111", w.b)
    c = w.client(w.desk)
    assert c.get(f"/api/members/{bina.id}/").status_code == 404
    r = c.post("/api/subscriptions/", {"member": bina.id, "plan": w.monthly.id}, format="json")
    assert r.status_code == 400 and "member" in r.json()["error"]["fields"]
    r = c.post("/api/payments/", {"member": bina.id, "amount_paise": 50000, "method": "cash"}, format="json")
    assert r.status_code == 400 and "member" in r.json()["error"]["fields"]
    parts = [{"method": "cash", "amount_paise": 100}, {"method": "upi", "amount_paise": 100}]
    r = c.post("/api/payments/split/", {"member": bina.id, "parts": parts}, format="json")
    assert r.status_code == 400 and "member" in r.json()["error"]["fields"]
    assert not bina.payments.exists() and not bina.subscriptions.exists()
    # their own branch's member still works, and admins reach every branch
    assert c.post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id}, format="json").status_code == 201
    assert w.client(w.admin).post("/api/subscriptions/", {"member": bina.id, "plan": w.monthly.id}, format="json").status_code == 201


def test_staff_see_only_the_people_at_their_branches(w):
    trainer_b = w.role("trainerb@x.in", "trainer", [w.b])
    names = lambda role: {s["name"] for s in w.client(role).get("/api/staff/").json()["results"]}  # noqa: E731
    assert names(w.desk) == names(w.trainer) == {"Desk0", "Trainer0"}
    assert names(w.desk_b) == {"Deskb0", "Trainerb"}
    assert names(w.admin) == {"Admin0", "Desk0", "Deskb0", "Trainer0", "Trainerb"}
    assert w.client(w.desk).get(f"/api/staff/{trainer_b.id}/").status_code == 404


def test_desk_picks_only_a_trainer_at_its_branches(w):
    trainer_b = w.role("trainerb@x.in", "trainer", [w.b])
    pt = w.monthly.__class__.objects.create(gym=w.gym, name="PT 8", kind="pt", months=1, sessions=8, price_paise=400000)
    c = w.client(w.desk)
    r = c.post("/api/subscriptions/", {"member": w.member.id, "plan": pt.id, "trainer": trainer_b.id}, format="json")
    assert r.status_code == 400 and "trainer" in r.json()["error"]["fields"]
    r = c.patch(f"/api/members/{w.member.id}/", {"trainer": trainer_b.id}, format="json")
    assert r.status_code == 400 and "trainer" in r.json()["error"]["fields"]
    assert c.patch(f"/api/members/{w.member.id}/", {"trainer": w.trainer.id}, format="json").status_code == 200
    assert w.client(w.admin).patch(f"/api/members/{w.member.id}/", {"trainer": trainer_b.id}, format="json").status_code == 200



def test_members_filter_by_current_plan(w):
    from apps.members.models import Plan
    from apps.members.services import sell

    annual = Plan.objects.create(gym=w.gym, name="Annual", months=12, price_paise=1200000)
    switched = w.plan_ending_on(w.today - timedelta(days=40), "Bina", "9811111112")  # old monthly, now on annual
    sell(switched, annual, by=w.desk, starts=w.today - timedelta(days=5))
    c = w.client(w.admin)
    names = lambda url: [m["name"] for m in c.get(url).json()["results"]]  # noqa: E731
    assert names(f"/api/members/?plan={w.monthly.id}") == ["Asha"]
    assert names(f"/api/members/?plan={annual.id}") == ["Bina"]
    assert names(f"/api/members/?plan={annual.id}&status=due") == ["Bina"]
    assert names(f"/api/members/?plan={annual.id}&status=active") == []
    assert names(f"/api/members/?plan={annual.id}&branch={w.b.id}") == []

def test_members_sorted_by_name_or_newest(w):
    from apps.members.models import Member

    for name, phone, joined in (("Zoya", "9811111121", 2), ("Bina", "9811111122", 30), ("Chetan", "9811111123", 2)):
        m = w.new_member(name, phone, w.a)
        Member.objects.filter(pk=m.pk).update(joined_on=w.today - timedelta(days=joined))
    Member.objects.filter(pk=w.member.pk).update(joined_on=w.today)
    c = w.client(w.admin)
    names = lambda url: [m["name"] for m in c.get(url).json()["results"]]  # noqa: E731
    assert names("/api/members/") == ["Asha", "Bina", "Chetan", "Zoya"]
    assert names("/api/members/?sort=newest") == ["Asha", "Chetan", "Zoya", "Bina"]  # same day: the one added last first
    assert names("/api/members/?sort=newest&status=none") == ["Chetan", "Zoya", "Bina"]  # the status filter keeps the order


def test_trainer_sees_own_members_without_amounts(w):
    rows = w.client(w.trainer).get("/api/members/").json()["results"]
    assert rows[0]["name"] == "Asha"
    assert "balance_paise" not in rows[0] and rows[0]["payment_due"] is False
    assert w.client(w.trainer).get(f"/api/subscriptions/?member={w.member.id}").status_code == 403
    assert w.client(w.trainer).get("/api/payments/").status_code == 403


def test_member_sees_only_self(w):
    w.new_member("Bina", "9811111111", w.a)
    w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    u = User.objects.get(phone=w.member.phone)
    from rest_framework.test import APIClient

    c = APIClient()
    c.force_authenticate(u)
    c.credentials(HTTP_X_GYM="iron")
    rows = c.get("/api/members/").json()["results"]
    assert [r["name"] for r in rows] == ["Asha"]
    assert c.post("/api/payments/", {}).status_code == 403


def test_member_signs_in_with_their_username_not_their_phone(w, client):
    r = w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    assert r.json() == {"username": "asha", "name": "Asha", "linked": False}  # made from their name
    login = lambda name: client.post("/api/auth/login/", {"username": name, "password": "secret1"}, content_type="application/json")
    assert login("@Asha").status_code == 200
    assert login("98000 00001").status_code == 401  # a phone is contact only: families share them


def test_only_admin_manages_staff(w):
    assert w.client(w.desk).post("/api/staff/", {}, format="json").status_code == 403


def test_support_needs_a_window_and_is_read_only(w):
    sup = User.objects.create_user(email="help@dumbelo.com", password="x", name="Support", is_staff=True)
    from rest_framework.test import APIClient

    c = APIClient()
    c.force_authenticate(sup)
    c.credentials(HTTP_X_GYM="iron")
    assert c.get("/api/members/").status_code == 404
    SupportAccess.objects.create(gym=w.gym, granted_by=w.admin.user, ends=timezone.now() + timedelta(hours=2))
    assert c.get("/api/members/").status_code == 200
    assert c.post("/api/branches/", {"name": "X"}, format="json").status_code == 403


def test_staff_create_and_owner_protected(w):
    c = w.client(w.admin)
    r = c.post("/api/staff/", {"name": "Ravi", "email": "ravi@x.in", "role": "trainer", "branches": [w.b.id], "password": "longpass1"}, format="json")
    assert r.status_code == 201, r.json()
    assert c.delete(f"/api/staff/{w.admin.id}/").status_code == 400


def test_member_sees_own_plan_and_balance(w):
    w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    from rest_framework.test import APIClient

    c = APIClient()
    c.force_authenticate(User.objects.get(phone=w.member.phone))
    c.credentials(HTTP_X_GYM="iron")
    me = c.get("/api/members/").json()["results"][0]
    assert me["plan"]["name"] == "Monthly" and me["balance_paise"] == 0
    assert c.get(f"/api/checkins/?member={w.member.id}").status_code == 200


def test_member_sees_own_plans_and_payments_only(w):
    from apps.members.models import Payment, Subscription
    from apps.members.services import sell, take_payment

    other = w.new_member("Bina", "9811111111", w.a)
    take_payment(other, 50000, "cash", by=w.desk, subscription=sell(other, w.monthly, by=w.desk))
    mine = Subscription.objects.get(member=w.member)
    renewal = sell(w.member, w.monthly, by=w.desk)  # starts after the current plan: up next
    take_payment(w.member, 10000, "cash", by=w.desk, note="Owner's friend, gave discount")
    Payment.objects.filter(member=w.member, amount_paise=10000).update(voided=True, void_reason="Entered twice")
    dropped = sell(w.member, w.monthly, by=w.desk)
    dropped.cancelled = True
    dropped.save(update_fields=["cancelled"])
    c = w.member_client()

    assert c.get(f"/api/subscriptions/?member={other.id}").json()["results"] == []  # another member's id finds nothing
    plans = c.get("/api/subscriptions/").json()["results"]
    assert [p["id"] for p in plans] == [renewal.id, mine.id]  # newest first, the cancelled one left out
    assert plans[1]["plan_name"] == "Monthly" and plans[1]["paid_paise"] == 150000
    assert c.get(f"/api/subscriptions/{other.subscriptions.get().id}/").status_code == 404

    pays = c.get("/api/payments/").json()["results"]
    assert len(pays) == 1 and pays[0]["amount_paise"] == 150000 and pays[0]["plan_name"] == "Monthly"  # the voided one left out
    assert "note" not in pays[0] and "void_reason" not in pays[0]
    assert c.get("/api/payments/?from=2020-01-01").status_code == 200  # any dates: they're all their own

    # Reading only: the desk's money and every change stay the desk's.
    assert c.get("/api/payments/collection/").status_code == 403
    assert c.post(f"/api/subscriptions/{mine.id}/freeze/", {"until": str(w.today)}, format="json").status_code == 403
    assert c.post(f"/api/payments/{pays[0]['id']}/void/", {"reason": "x"}, format="json").status_code == 403
    assert c.post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id}, format="json").status_code == 403


def test_trainer_attention_filter(w):
    lapsed = w.new_member("Ravi", "9822222222", w.a, trainer=w.trainer)  # no plan: status "none"
    rows = w.client(w.trainer).get("/api/members/?status=attention").json()["results"]
    assert [r["id"] for r in rows] == [lapsed.id]
