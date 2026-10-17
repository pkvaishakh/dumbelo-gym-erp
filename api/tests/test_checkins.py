from datetime import datetime, time, timedelta

from apps.attendance.models import CheckIn, Device
from apps.core import clock


def test_desk_checks_in_member_once_a_day(w):
    c = w.client(w.desk)
    r = c.post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json")
    assert r.status_code == 201 and r.json()["kind"] == "member"
    r = c.post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_checked_in"


def test_expired_member_is_turned_away(w):
    m = w.new_member("Old", "9822222222", w.a)
    from apps.members.services import sell

    sell(m, w.monthly, by=w.desk, starts=w.today - timedelta(days=90))
    r = w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": m.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "membership_expired"


def test_receptionist_cannot_check_in_at_other_branch(w):
    r = w.client(w.desk).post("/api/checkins/", {"branch": w.b.id, "member": w.member.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "wrong_branch"


def test_staff_check_in_and_counts_by_role(w):
    c = w.client(w.desk)
    assert c.post("/api/checkins/", {"branch": w.a.id, "staff": w.trainer.id}, format="json").status_code == 201
    assert c.post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json").status_code == 201
    s = w.client(w.admin).get("/api/checkins/summary/").json()
    assert s["totals"]["trainer"] == 1 and s["totals"]["member"] == 1
    rows = w.client(w.admin).get("/api/checkins/?kind=trainer").json()["results"]
    assert [r["name"] for r in rows] == [w.trainer.user.name]


def test_trainer_cannot_check_in_at_branch_they_dont_work(w):
    r = w.client(w.desk_b).post("/api/checkins/", {"branch": w.b.id, "staff": w.trainer.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "wrong_branch"


def test_session_is_the_one_the_time_falls_in_or_the_next(w):
    from apps.attendance.services import check_in, session_name

    tz = clock.tz(w.gym)
    day = w.today - timedelta(days=1)
    c1 = check_in(w.a, member=w.member, source="desk", at=datetime.combine(day, time(6, 30), tzinfo=tz))
    assert session_name(c1, w.gym) == "Morning"
    c2 = check_in(w.a, staff=w.trainer, source="desk", at=datetime.combine(day, time(15, 40), tzinfo=tz))
    assert session_name(c2, w.gym) == "Evening"  # in the break: counts toward the next session


def test_qr_check_in(w):
    w.client(w.desk).post(f"/api/members/{w.member.id}/set-login/", {"password": "secret1"}, format="json")
    from rest_framework.test import APIClient

    from apps.accounts.models import User

    c = APIClient()
    c.force_authenticate(User.objects.get(phone=w.member.phone))
    r = c.post("/api/checkins/qr/", {"code": w.a.qr_code}, format="json")
    assert r.status_code == 201 and r.json()["source"] == "qr"
    assert c.post("/api/checkins/qr/", {"code": "nope"}, format="json").status_code == 409


def test_device_punch(w, client):
    d = Device.objects.create(branch=w.a, name="Turnstile", serial="ZK1")
    w.member.device_user_id = "77"
    w.member.save()
    r = client.post("/api/devices/punch/", {"user_id": "77"}, content_type="application/json", HTTP_X_DEVICE_TOKEN=d.token)
    assert r.json() == {"open": True, "recorded": True, "checkin": CheckIn.objects.get().id}
    r = client.post("/api/devices/punch/", {"user_id": "77"}, content_type="application/json", HTTP_X_DEVICE_TOKEN=d.token)
    assert r.json()["open"] is True and r.json()["recorded"] is False
    assert client.post("/api/devices/punch/", {"user_id": "77"}, content_type="application/json", HTTP_X_DEVICE_TOKEN="bad").status_code == 401
    assert client.post("/api/devices/punch/", {"user_id": "5"}, content_type="application/json", HTTP_X_DEVICE_TOKEN=d.token).json()["open"] is False


def test_summary_counts_member_check_ins_by_source(w):
    from apps.attendance.models import CheckIn
    from apps.attendance.services import check_in

    check_in(w.a, member=w.member, source=CheckIn.QR)
    check_in(w.a, staff=w.trainer, source=CheckIn.DESK)
    r = w.client(w.desk).get("/api/checkins/summary/").json()
    assert r["member_sources"] == {"desk": 0, "qr": 1, "device": 0}
    assert r["totals"]["member"] == 1 and r["totals"]["trainer"] == 1


def test_summary_without_branch_counts_each_branch(w):
    from apps.attendance.models import CheckIn
    from apps.attendance.services import check_in

    from apps.members.services import sell

    bee = w.new_member("Bee", "9833333333", w.b)
    sell(bee, w.monthly, by=w.admin)
    check_in(w.a, member=w.member, source=CheckIn.DEVICE)
    check_in(w.b, member=bee, source=CheckIn.QR)
    r = w.client(w.admin).get("/api/checkins/summary/").json()
    by = {b["id"]: b for b in r["branches"]}
    assert by[w.a.id]["member"] == 1 and by[w.a.id]["member_sources"]["device"] == 1
    assert by[w.b.id]["member"] == 1 and by[w.b.id]["member_sources"]["qr"] == 1
    assert r["totals"]["member"] == 2
    assert "branches" not in w.client(w.admin).get(f"/api/checkins/summary/?branch={w.a.id}").json()
    assert [b["id"] for b in w.client(w.desk).get("/api/checkins/summary/").json()["branches"]] == [w.a.id]
