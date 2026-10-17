from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.gyms.models import SupportAccess


def test_login_and_me(w, client):
    r = client.post("/api/auth/login/", {"identifier": "admin0@x.in", "password": "pass12345"}, content_type="application/json")
    assert r.status_code == 200
    me = client.get("/api/me/", HTTP_AUTHORIZATION="Bearer " + r.json()["access"]).json()
    assert me["roles"][0]["gym"] == "iron" and me["roles"][0]["role"] == "admin"
    assert {b["name"] for b in me["roles"][0]["branches"]} == {"A", "B"}


def test_wrong_password(w, client):
    r = client.post("/api/auth/login/", {"identifier": "admin0@x.in", "password": "nope"}, content_type="application/json")
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


def test_member_can_sign_in_with_phone(w, client):
    w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    r = client.post("/api/auth/login/", {"identifier": "98000 00001", "password": "secret1"}, content_type="application/json")
    assert r.status_code == 200


def test_only_admin_manages_staff(w):
    assert w.client(w.desk).post("/api/staff/", {}, format="json").status_code == 403


def test_support_needs_a_window_and_is_read_only(w):
    sup = User.objects.create_user(email="help@rackline.in", password="x", name="Support", is_staff=True)
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


def test_trainer_attention_filter(w):
    lapsed = w.new_member("Ravi", "9822222222", w.a, trainer=w.trainer)  # no plan: status "none"
    rows = w.client(w.trainer).get("/api/members/?status=attention").json()["results"]
    assert [r["id"] for r in rows] == [lapsed.id]
