"""The Device API: who may manage turnstiles, and what happens at the door when a token changes."""
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.attendance.models import Device
from apps.audit.models import AuditLog


def member_client(w):
    """A signed-in member of the gym, to prove members can't reach the device list."""
    w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    c = APIClient()
    c.force_authenticate(User.objects.get(phone=w.member.phone))
    c.credentials(HTTP_X_GYM=w.gym.slug)
    return c


def add(client, branch, name="Front door", serial="ZK-1"):
    return client.post("/api/devices/", {"branch": branch.id, "name": name, "serial": serial}, format="json")


def punch(client, token, user_id="77"):
    return client.post("/api/devices/punch/", {"user_id": user_id}, content_type="application/json", HTTP_X_DEVICE_TOKEN=token)


def test_admin_adds_a_device_and_gets_the_token_once(w):
    c = w.client(w.admin)
    r = add(c, w.a)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["token"] and body["is_active"] is True and body["last_seen"] is None
    assert body["branch"] == w.a.id and body["branch_name"] == "A"

    rows = c.get("/api/devices/").json()["results"]
    assert [(d["name"], d["serial"]) for d in rows] == [("Front door", "ZK-1")]
    assert "token" not in rows[0]  # the token is shown once, at the moment it is created
    assert "token" not in c.get(f"/api/devices/{body['id']}/").json()


def test_devices_are_admin_only(w):
    Device.objects.create(branch=w.a, name="Front door", serial="ZK-1")
    for who in (w.desk, w.trainer):
        c = w.client(who)
        assert c.get("/api/devices/").status_code == 403
        assert add(c, w.a, serial="ZK-9").status_code == 403
    m = member_client(w)
    assert m.get("/api/devices/").status_code == 403
    assert add(m, w.a, serial="ZK-9").status_code == 403


def test_another_gyms_device_is_not_found(w, other):
    theirs = Device.objects.create(branch=other.a, name="Theirs", serial="ZK-OTHER")
    c = w.client(w.admin)
    assert c.get(f"/api/devices/{theirs.id}/").status_code == 404
    assert c.patch(f"/api/devices/{theirs.id}/", {"name": "Mine now"}, format="json").status_code == 404
    assert c.post(f"/api/devices/{theirs.id}/deactivate/").status_code == 404
    assert c.post(f"/api/devices/{theirs.id}/rotate-token/").status_code == 404
    assert c.get("/api/devices/").json()["count"] == 0  # and it isn't in the list


def test_a_device_cannot_be_put_in_another_gyms_branch(w, other):
    r = w.client(w.admin).post("/api/devices/", {"branch": other.a.id, "name": "X", "serial": "ZK-2"}, format="json")
    assert r.status_code == 400 and "branch" in r.json()["error"]["fields"]


def test_branch_filter(w):
    Device.objects.create(branch=w.a, name="A door", serial="ZK-A")
    Device.objects.create(branch=w.b, name="B door", serial="ZK-B")
    c = w.client(w.admin)
    assert [d["name"] for d in c.get(f"/api/devices/?branch={w.b.id}").json()["results"]] == ["B door"]
    assert c.get("/api/devices/?branch=abc").status_code == 400


def test_rename_and_move_a_device_but_not_its_serial(w):
    d = Device.objects.create(branch=w.a, name="Front door", serial="ZK-1")
    r = w.client(w.admin).patch(f"/api/devices/{d.id}/", {"name": "Back door", "branch": w.b.id, "serial": "ZK-NEW"}, format="json")
    assert r.status_code == 200
    d.refresh_from_db()
    assert (d.name, d.branch_id, d.serial) == ("Back door", w.b.id, "ZK-1")


def test_the_same_serial_twice_is_a_field_error(w):
    c = w.client(w.admin)
    assert add(c, w.a).status_code == 201
    r = add(c, w.b, name="Other door")
    assert r.status_code == 400 and "serial" in r.json()["error"]["fields"]


def test_a_device_is_never_deleted(w):
    d = Device.objects.create(branch=w.a, name="Front door", serial="ZK-1")
    assert w.client(w.admin).delete(f"/api/devices/{d.id}/").status_code == 405
    assert Device.objects.filter(pk=d.id).exists()


def test_deactivated_token_is_refused_at_the_door(w, client):
    c = w.client(w.admin)
    d = Device.objects.create(branch=w.a, name="Front door", serial="ZK-1")
    w.member.device_user_id = "77"
    w.member.save()
    assert punch(client, d.token).json()["open"] is True

    r = c.post(f"/api/devices/{d.id}/deactivate/")
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert punch(client, d.token).status_code == 401
    # switching off a device that is already off says so instead of pretending
    assert c.post(f"/api/devices/{d.id}/deactivate/").json()["error"]["code"] == "already_off"


def test_rotating_a_token_refuses_the_old_one(w, client):
    d = Device.objects.create(branch=w.a, name="Front door", serial="ZK-1")
    w.member.device_user_id = "77"
    w.member.save()
    old = d.token

    r = w.client(w.admin).post(f"/api/devices/{d.id}/rotate-token/")
    assert r.status_code == 200
    new = r.json()["token"]
    assert new and new != old
    assert punch(client, old).status_code == 401
    assert punch(client, new).json()["open"] is True


def test_add_deactivate_and_rotate_are_audited_without_the_token(w):
    c = w.client(w.admin)
    d = Device.objects.get(pk=add(c, w.a).json()["id"])
    c.post(f"/api/devices/{d.id}/rotate-token/")
    c.post(f"/api/devices/{d.id}/deactivate/")

    rows = AuditLog.objects.filter(gym=w.gym, object_type="Device", object_id=str(d.id))
    assert set(rows.values_list("action", flat=True)) == {"device.added", "device.token_rotated", "device.deactivated"}
    assert all(row.actor == w.admin.user for row in rows)
    d.refresh_from_db()
    assert d.token not in str(list(rows.values_list("before", "after")))


def test_device_list_stays_within_a_query_budget(w, django_assert_max_num_queries):
    c = w.client(w.admin)
    for i in range(3):
        Device.objects.create(branch=w.a, name=f"Door {i}", serial=f"ZK-{i}")
    with django_assert_max_num_queries(6) as few:
        assert c.get("/api/devices/").status_code == 200
    for i in range(3, 15):
        Device.objects.create(branch=w.b, name=f"Door {i}", serial=f"ZK-{i}")
    with django_assert_max_num_queries(len(few.captured_queries)):
        assert c.get("/api/devices/").json()["count"] == 15
