"""Your own account details and password, and an admin resetting a staff member's password."""
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.models import AuditLog
from apps.gyms.models import GymRole


def signed_in(user):
    """A client signed in the real way, with a refresh token the server knows about."""
    token = RefreshToken.for_user(user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return c, str(token)


def refresh_works(token):
    return APIClient().post("/api/auth/refresh/", {"refresh": token}, format="json").status_code == 200


def test_staff_edit_their_own_details(w):
    r = w.client(w.admin).patch("/api/me/", {"name": "Meera S", "email": "Meera@New.in", "phone": "98111 22233"}, format="json")
    assert r.status_code == 200, r.content
    assert (r.json()["name"], r.json()["email"], r.json()["phone"]) == ("Meera S", "Meera@new.in", "+919811122233")
    w.admin.user.refresh_from_db()
    assert w.admin.user.email == "Meera@new.in"


def test_email_and_phone_must_be_free(w):
    w.desk.user.phone = "+919811122233"
    w.desk.user.save()
    r = w.client(w.admin).patch("/api/me/", {"email": w.desk.user.email.upper(), "phone": "9811122233"}, format="json")
    assert r.status_code == 400
    assert set(r.json()["error"]["fields"]) == {"email", "phone"}
    r = w.client(w.admin).patch("/api/me/", {"phone": "12345"}, format="json")
    assert r.json()["error"]["fields"]["phone"] == ["Enter a 10-digit mobile number"]


def test_members_details_are_changed_by_the_desk(w):
    r = w.member_client().patch("/api/me/", {"name": "Someone"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "details_by_desk"


def test_change_own_password_signs_out_other_devices(w):
    user = w.admin.user
    c, old = signed_in(user)
    r = c.post("/api/me/password/", {"current_password": "pass12345", "new_password": "Iron-house-2026"}, format="json")
    assert r.status_code == 200, r.content
    assert not refresh_works(old)
    assert refresh_works(r.json()["refresh"])
    user.refresh_from_db()
    assert user.check_password("Iron-house-2026")


def test_change_own_password_checks_the_current_one(w):
    c = w.client(w.admin)
    r = c.post("/api/me/password/", {"current_password": "nope", "new_password": "Iron-house-2026"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "wrong_password"
    r = c.post("/api/me/password/", {"current_password": "pass12345", "new_password": "password"}, format="json")
    assert r.status_code == 400 and "new_password" in r.json()["error"]["fields"]


def test_admin_resets_a_receptionists_password(w):
    _, old = signed_in(w.desk.user)
    r = w.client(w.admin).post(f"/api/staff/{w.desk.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 204, r.content
    w.desk.user.refresh_from_db()
    assert w.desk.user.check_password("Front-desk-77")
    assert not refresh_works(old)
    log = AuditLog.objects.get(action="staff.password_reset")
    assert log.object_id == str(w.desk.id) and "Front-desk-77" not in str(log.before) + str(log.after)


def test_only_admins_reset_and_never_an_admins(w):
    r = w.client(w.desk).post(f"/api/staff/{w.trainer.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 403
    other_admin = w.role("second@x.in", GymRole.ADMIN, [])
    r = w.client(other_admin).post(f"/api/staff/{w.admin.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "admin_password"


def test_no_reset_for_a_login_shared_with_another_gym(w, other):
    GymRole.objects.create(user=w.trainer.user, gym=other.gym, role=GymRole.TRAINER)
    r = w.client(w.admin).post(f"/api/staff/{w.trainer.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"
    w.trainer.user.refresh_from_db()
    assert w.trainer.user.check_password("pass12345")


def test_another_gyms_staff_is_not_found(w, other):
    r = w.client(w.admin).post(f"/api/staff/{other.desk.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 404


def test_no_editing_the_details_of_a_login_shared_with_another_gym(w, other):
    GymRole.objects.create(user=w.trainer.user, gym=other.gym, role=GymRole.TRAINER)
    admin = w.client(w.admin)
    r = admin.patch(f"/api/staff/{w.trainer.id}/", {"email": "taken-over@x.in"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"
    email = w.trainer.user.email
    w.trainer.user.refresh_from_db()
    assert w.trainer.user.email == email
    # Their work at this gym can still be changed, and resending their details unchanged is fine.
    r = admin.patch(f"/api/staff/{w.trainer.id}/", {"shift": "Mornings", "email": email, "name": w.trainer.user.name}, format="json")
    assert r.status_code == 200, r.content


def test_receptionist_changes_own_password(w):
    r = w.client(w.desk).post("/api/me/password/", {"current_password": "pass12345", "new_password": "Front-desk-77"}, format="json")
    assert r.status_code == 200, r.content
