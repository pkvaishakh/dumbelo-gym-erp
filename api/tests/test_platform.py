"""Dumbelo's side: the Console's gyms and their admins, who may use it, and what a suspended gym can still do."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.attendance.models import Device
from apps.audit.models import AuditLog
from apps.core.tenancy import InGym
from apps.gyms.models import Gym, GymRole
from apps.platform.services import create_gym

GYMS = "/api/platform/gyms/"
NEW_GYM = {
    "name": "Pulse Fitness", "slug": "pulse", "branch": "Kochi", "owner_name": "Anil Menon",
    "owner_email": "anil@pulse.in", "owner_password": "first-pass-123",
}


def dumbelo(email="ops@dumbelo.com", **extra):
    user = User.objects.create_superuser(email=email, password="pass12345", name="Dumbelo Ops", **extra)
    c = APIClient()
    c.force_authenticate(user)
    return c


def support():
    """Dumbelo support: `is_staff` without `is_superuser`. It reads inside a gym's window, never the Console."""
    user = User.objects.create_user(email="help@dumbelo.com", password="pass12345", name="Ravi at Dumbelo", is_staff=True)
    c = APIClient()
    c.force_authenticate(user)
    return c


def suspend(w):
    w.gym.status = Gym.SUSPENDED
    w.gym.save()


def admins(c, gym):
    return c.get(f"{GYMS}{gym.id}/admins/").json()


def test_only_dumbelo_admins_reach_the_console(w):
    refused = [w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client(), support()]
    for c in refused:
        assert c.get(GYMS).status_code == 403
        assert c.get(f"{GYMS}{w.gym.id}/").status_code == 403
        assert c.post(GYMS, NEW_GYM, format="json").status_code == 403
        assert c.post(f"{GYMS}{w.gym.id}/suspend/", {"reason": "x"}, format="json").status_code == 403
        assert c.get(f"{GYMS}{w.gym.id}/admins/").status_code == 403
        assert c.post(f"{GYMS}{w.gym.id}/admins/{w.admin.id}/make-owner/").status_code == 403
    assert APIClient().get(GYMS).status_code == 401
    inactive = dumbelo("gone@dumbelo.com", is_active=False)
    assert inactive.get(GYMS).status_code == 403
    assert dumbelo().get(GYMS).status_code == 200


def test_me_says_who_runs_the_console(w):
    assert w.client(w.admin).get("/api/me/").json()["is_dumbelo_admin"] is False
    me = dumbelo().get("/api/me/").json()
    assert me["is_dumbelo_admin"] is True and me["roles"] == []


def test_new_gym_owner_can_sign_in(prices, client):
    c = dumbelo()
    r = c.post(GYMS, NEW_GYM, format="json")
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["status"] == "trial" and body["owner_email"] == "anil@pulse.in" and body["owner_new_login"] is True
    assert body["billing_email"] == "anil@pulse.in"  # the owner's, when none is given
    assert [b["name"] for b in body["branches"]] == ["Kochi"] and body["branch_count"] == 1
    assert "owner_password" not in body

    login = client.post("/api/auth/login/", {"identifier": "anil@pulse.in", "password": "first-pass-123"}, content_type="application/json")
    assert login.status_code == 200
    me = client.get("/api/me/", HTTP_AUTHORIZATION="Bearer " + login.json()["access"]).json()
    assert me["roles"][0]["gym"] == "pulse" and me["roles"][0]["role"] == "admin" and me["roles"][0]["is_owner"] is True
    gym = Gym.objects.get(slug="pulse")
    assert gym.branches.get().sessions.count() == 1  # open all day until the gym sets its hours

    row = AuditLog.objects.get(action="gym.created")
    assert row.gym == gym and row.actor.email == "ops@dumbelo.com"
    assert "first-pass-123" not in str(row.after)


def test_new_gym_can_use_an_existing_login(w):
    c = dumbelo()
    r = c.post(GYMS, {**NEW_GYM, "owner_email": "ADMIN0@x.in", "owner_name": "", "owner_password": ""}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["owner_new_login"] is False and r.json()["owner_name"] == w.admin.user.name
    assert w.admin.user.gym_roles.count() == 2
    w.admin.user.refresh_from_db()
    assert w.admin.user.check_password("pass12345")  # they keep their own password


def test_new_gym_form_errors(w):
    c = dumbelo()
    r = c.post(GYMS, {**NEW_GYM, "slug": "iron", "timezone": "Mars/Base"}, format="json")
    assert r.status_code == 400
    assert set(r.json()["error"]["fields"]) == {"slug", "timezone"}
    r = c.post(GYMS, {**NEW_GYM, "slug": "Bad Slug!"}, format="json")
    assert "slug" in r.json()["error"]["fields"]
    r = c.post(GYMS, {**NEW_GYM, "owner_name": "", "owner_password": ""}, format="json")
    assert set(r.json()["error"]["fields"]) == {"owner_name", "owner_password"}  # a new login needs both
    r = c.post(GYMS, {**NEW_GYM, "owner_email": "ops@dumbelo.com"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "dumbelo_login"
    assert not Gym.objects.filter(slug="pulse").exists()


def test_create_gym_command_uses_the_same_service(prices, capsys):
    call_command("create_gym", "--name", "Pulse", "--slug", "pulse", "--branch", "Kochi", "--owner-email", "anil@pulse.in", "--owner-name", "Anil")
    out = capsys.readouterr().out
    password = out.split("first password: ")[1].split()[0]
    owner = GymRole.objects.get(gym__slug="pulse", is_owner=True)
    assert owner.role == GymRole.ADMIN and owner.user.check_password(password)
    assert AuditLog.objects.get(action="gym.created").actor is None


def test_gyms_list_search_status_and_counts(w, other, django_assert_max_num_queries):
    for i in range(6):
        create_gym(name=f"Gym {i}", slug=f"gym-{i}", timezone_name="Asia/Kolkata", branch="Main", owner_email=f"o{i}@g.in", owner_name="Owner", owner_password="first-pass-123")
    suspend(other)
    c = dumbelo()
    with django_assert_max_num_queries(4):
        body = c.get(GYMS).json()
    assert body["count"] == 8
    iron = next(g for g in body["results"] if g["slug"] == "iron")
    assert iron["branch_count"] == 2 and iron["member_count"] == 1 and iron["owner_email"] == "admin0@x.in"
    assert "phone" not in iron and "balance_paise" not in iron  # never what is inside the gym

    assert [g["slug"] for g in c.get(GYMS, {"q": "STEEL"}).json()["results"]] == ["steel"]
    assert c.get(GYMS, {"q": "g"}).json()["count"] == 8  # one character searches nothing
    assert [g["slug"] for g in c.get(GYMS, {"status": "suspended"}).json()["results"]] == ["steel"]
    assert c.get(GYMS, {"status": "closed"}).status_code == 400
    assert c.get(f"{GYMS}99999/").status_code == 404


def test_gym_screen_shows_branches_and_edits_are_audited(w):
    c = dumbelo()
    r = c.get(f"{GYMS}{w.gym.id}/")
    assert {b["name"]: b["member_count"] for b in r.json()["branches"]} == {"A": 1, "B": 0}
    r = c.patch(f"{GYMS}{w.gym.id}/", {"name": "Iron House Kochi", "timezone": "Asia/Dubai", "slug": "hacked"}, format="json")
    assert r.status_code == 200 and r.json()["name"] == "Iron House Kochi" and r.json()["slug"] == "iron"
    row = AuditLog.objects.get(action="gym.changed")
    assert row.gym == w.gym and row.before["timezone"] == "Asia/Kolkata" and row.after["timezone"] == "Asia/Dubai"
    assert c.put(f"{GYMS}{w.gym.id}/", {"name": "X"}, format="json").status_code == 405
    assert c.delete(f"{GYMS}{w.gym.id}/").status_code == 405  # gyms are suspended, never deleted


def test_suspend_and_activate_with_a_reason(w):
    c = dumbelo()
    assert c.post(f"{GYMS}{w.gym.id}/suspend/", {"reason": " "}, format="json").status_code == 400
    r = c.post(f"{GYMS}{w.gym.id}/suspend/", {"reason": "October invoice unpaid"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "suspended" and r.json()["status_reason"] == "October invoice unpaid"
    again = c.post(f"{GYMS}{w.gym.id}/suspend/", {"reason": "again"}, format="json")
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_suspended"
    r = c.post(f"{GYMS}{w.gym.id}/activate/", {"reason": "Paid in full"}, format="json")
    assert r.json()["status"] == "active"
    rows = AuditLog.objects.filter(gym=w.gym, action__in=["gym.suspended", "gym.activated"]).order_by("at", "id")
    assert [(a.action, a.before["status"], a.after["status"], a.after["reason"]) for a in rows] == [
        ("gym.suspended", "active", "suspended", "October invoice unpaid"), ("gym.activated", "suspended", "active", "Paid in full"),
    ]


def test_suspended_gym_refuses_staff_and_members_but_admins_reach_me(w):
    suspend(w)
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client(), w.client(w.admin)):
        r = c.get("/api/members/")
        assert r.status_code == 403 and r.json()["error"]["code"] == "gym_suspended"
        assert "Contact Dumbelo" in r.json()["error"]["message"]
    me = w.client(w.admin).get("/api/me/")
    assert me.status_code == 200 and me.json()["roles"][0]["gym_status"] == "suspended"
    # The paused screen needs to know who you are, so /api/me/ answers everyone; the gym's endpoints don't.
    assert w.client(w.desk).get("/api/me/").json()["roles"][0]["gym_status"] == "suspended"


def test_a_suspended_gym_you_are_not_in_is_still_not_found(w, other):
    suspend(other)
    c = w.client(w.admin)
    c.credentials(HTTP_X_GYM="steel")
    assert c.get("/api/members/").status_code == 404


def test_views_open_when_suspended_let_admins_only(w):
    class DumbeloPlan(APIView):
        permission_classes = [InGym]
        open_when_suspended = True

        def get(self, request):
            from rest_framework.response import Response
            return Response({"ok": True})

    suspend(w)
    factory = APIRequestFactory()

    def call(role):
        from rest_framework.test import force_authenticate
        req = factory.get("/x/", HTTP_X_GYM="iron")
        force_authenticate(req, role.user)
        return DumbeloPlan.as_view()(req)

    assert call(w.admin).status_code == 200
    assert call(w.desk).status_code == 403


def test_suspended_gym_refuses_qr_and_turnstile_check_ins(w):
    suspend(w)
    r = w.member_client().post("/api/checkins/qr/", {"code": w.a.qr_code}, format="json")
    assert r.status_code == 403 and r.json()["error"]["code"] == "gym_suspended"
    device = Device.objects.create(branch=w.a, name="Door", serial="D-1")
    w.member.device_user_id = "7"
    w.member.save()
    r = APIClient().post("/api/devices/punch/", {"user_id": "7"}, format="json", HTTP_X_DEVICE_TOKEN=device.token)
    assert r.json()["open"] is False and r.json()["code"] == "gym_suspended"


def test_admins_list_and_add(w, other):
    c = dumbelo()
    rows = admins(c, w.gym)
    assert [(a["email"], a["is_owner"], a["other_gyms"]) for a in rows] == [("admin0@x.in", True, 0)]
    r = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "new@x.in", "name": "Nisha", "password": "first-pass-123"}, format="json")
    assert r.status_code == 201 and r.json()["is_owner"] is False
    shared = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "admin1@x.in"}, format="json")  # steel's owner, keeps their login
    assert shared.status_code == 201 and shared.json()["other_gyms"] == 1
    again = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "new@x.in"}, format="json")
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_admin"
    desk = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "desk0@x.in"}, format="json")
    assert desk.json()["error"]["code"] == "has_role"
    missing = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "nobody@x.in"}, format="json")
    assert set(missing.json()["error"]["fields"]) == {"name", "password"}
    assert AuditLog.objects.filter(gym=w.gym, action="admin.added").count() == 2
    assert c.get(f"{GYMS}99999/admins/").status_code == 404


def test_another_gyms_admin_is_not_found(w, other):
    c = dumbelo()
    assert c.post(f"{GYMS}{w.gym.id}/admins/{other.admin.id}/deactivate/").status_code == 404
    assert c.post(f"{GYMS}{w.gym.id}/admins/{w.desk.id}/deactivate/").status_code == 404  # admins only
    other.admin.refresh_from_db()
    assert other.admin.is_active


def test_owner_cannot_be_deactivated(w):
    c = dumbelo()
    r = c.post(f"{GYMS}{w.gym.id}/admins/{w.admin.id}/deactivate/")
    assert r.status_code == 409 and r.json()["error"]["code"] == "owner"
    w.admin.refresh_from_db()
    assert w.admin.is_active and w.admin.is_owner
    assert not AuditLog.objects.filter(action="admin.deactivated").exists()


def test_deactivate_reactivate_and_make_owner(w, client):
    c = dumbelo()
    second = c.post(f"{GYMS}{w.gym.id}/admins/", {"email": "second@x.in", "name": "Second", "password": "first-pass-123"}, format="json").json()
    r = c.post(f"{GYMS}{w.gym.id}/admins/{second['id']}/deactivate/")
    assert r.status_code == 200 and r.json()["is_active"] is False
    login = client.post("/api/auth/login/", {"identifier": "second@x.in", "password": "first-pass-123"}, content_type="application/json")
    c2 = APIClient()
    c2.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access"], HTTP_X_GYM="iron")
    assert c2.get("/api/members/").status_code == 404  # deactivated: the gym is closed to them
    assert c.post(f"{GYMS}{w.gym.id}/admins/{second['id']}/make-owner/").json()["error"]["code"] == "not_active"

    assert c.post(f"{GYMS}{w.gym.id}/admins/{second['id']}/reactivate/").json()["is_active"] is True
    r = c.post(f"{GYMS}{w.gym.id}/admins/{second['id']}/make-owner/")
    assert r.status_code == 200 and r.json()["is_owner"] is True
    w.admin.refresh_from_db()
    assert not w.admin.is_owner and w.admin.is_active  # the old owner stays an admin
    assert c.post(f"{GYMS}{w.gym.id}/admins/{w.admin.id}/deactivate/").status_code == 200  # no longer the owner
    made = AuditLog.objects.get(action="admin.made_owner")
    assert made.gym == w.gym and made.before == {"owner": "admin0@x.in"} and made.after == {"owner": "second@x.in"}
    assert set(AuditLog.objects.filter(gym=w.gym).values_list("action", flat=True)) == {
        "admin.added", "admin.deactivated", "admin.reactivated", "admin.made_owner",
    }


def test_reset_an_admins_password(w, client):
    c = dumbelo()
    url = f"{GYMS}{w.gym.id}/admins/{w.admin.id}/reset-password/"
    assert c.post(url, {"password": "123"}, format="json").status_code == 400
    assert c.post(url, {"password": "brand-new-pass-9"}, format="json").status_code == 204
    ok = client.post("/api/auth/login/", {"identifier": "admin0@x.in", "password": "brand-new-pass-9"}, content_type="application/json")
    assert ok.status_code == 200
    row = AuditLog.objects.get(action="admin.password_reset")
    assert row.gym == w.gym and "brand-new-pass-9" not in str(row.before) + str(row.after)


@pytest.mark.parametrize("path", ["deactivate", "make-owner", "reactivate"])
def test_admin_actions_answer_404_for_a_missing_gym(w, path):
    assert dumbelo().post(f"{GYMS}99999/admins/{w.admin.id}/{path}/").status_code == 404
