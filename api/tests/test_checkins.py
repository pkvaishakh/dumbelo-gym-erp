from datetime import datetime, time, timedelta

import pytest

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


def test_staff_see_their_own_check_ins_at_any_branch(w):
    tz = clock.tz(w.gym)
    days = [w.today - timedelta(days=n) for n in (0, 10, 40)]
    for d, branch in zip(days, (w.a, w.b, w.a)):  # branch B: where they worked before
        CheckIn.objects.create(gym=w.gym, branch=branch, staff=w.trainer, at=datetime.combine(d, time(6, 0), tzinfo=tz), local_date=d, source="desk")
    CheckIn.objects.create(gym=w.gym, branch=w.a, staff=w.desk, at=datetime.combine(w.today, time(6, 0), tzinfo=tz), local_date=w.today, source="desk")
    c = w.client(w.trainer)
    rows = c.get("/api/checkins/", {"mine": "true"}).json()["results"]
    assert [(r["local_date"], r["branch_name"]) for r in rows] == [(str(days[0]), "A"), (str(days[1]), "B"), (str(days[2]), "A")]
    month = c.get("/api/checkins/", {"mine": "true", "from": str(w.today - timedelta(days=30)), "to": str(w.today)}).json()
    assert month["count"] == 2
    assert [r["name"] for r in w.client(w.desk).get("/api/checkins/", {"mine": "true"}).json()["results"]] == [w.desk.user.name]


def test_trainer_cannot_check_in_at_branch_they_dont_work(w):
    r = w.client(w.admin).post("/api/checkins/", {"branch": w.b.id, "staff": w.trainer.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "wrong_branch"


def test_desk_checks_in_only_its_own_branches_people(w):
    desk_b = w.client(w.desk_b)
    for who in ({"member": w.member.id}, {"staff": w.trainer.id}):  # branch A's member and trainer
        r = desk_b.post("/api/checkins/", {"branch": w.b.id, **who}, format="json")
        assert r.status_code == 409 and r.json()["error"]["code"] == "not_found"
    trainer_b = w.role("trainerb@x.in", "trainer", [w.b])
    assert desk_b.post("/api/checkins/", {"branch": w.b.id, "staff": trainer_b.id}, format="json").status_code == 201


def test_one_members_visits_between_two_days(w):
    from apps.attendance.services import check_in

    tz = clock.tz(w.gym)
    days = [w.today - timedelta(days=n) for n in (0, 10, 40)]
    for d in days:
        check_in(w.a, member=w.member, source="desk", at=datetime.combine(d, time(7, 0), tzinfo=tz))
    c = w.client(w.trainer)
    dates = lambda **p: [r["local_date"] for r in c.get("/api/checkins/", {"member": w.member.id, **p}).json()["results"]]
    assert dates() == [str(d) for d in days]
    assert dates(**{"from": str(w.today - timedelta(days=30)), "to": str(w.today)}) == [str(days[0]), str(days[1])]
    assert dates(**{"to": str(w.today - timedelta(days=5))}) == [str(days[1]), str(days[2])]
    backwards = c.get("/api/checkins/", {"member": w.member.id, "from": str(w.today), "to": str(days[2])})
    assert backwards.status_code == 400


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


def test_desk_corrects_todays_check_in_time(w):
    from apps.attendance.services import check_in
    from apps.audit.models import AuditLog

    c = check_in(w.a, member=w.member, source=CheckIn.DEVICE)
    r = w.client(w.desk).patch(f"/api/checkins/{c.id}/", {"time": "00:00"}, format="json")
    assert r.status_code == 200 and r.json()["time"] == "12:00 AM" and r.json()["local_date"] == str(w.today)
    c.refresh_from_db()
    assert clock.local(w.gym, c.at).time() == time(0, 0)
    log = AuditLog.objects.get(action="checkin.time_changed")
    assert log.object_id == str(c.id) and log.after == {"at": c.at.isoformat()} and log.before["at"] != log.after["at"]


def test_new_time_keeps_the_day_and_moves_the_session(w):
    from apps.attendance.services import check_in

    tz = clock.tz(w.gym)
    day = w.today - timedelta(days=1)
    c = check_in(w.a, staff=w.trainer, source="desk", at=datetime.combine(day, time(6, 30), tzinfo=tz))
    r = w.client(w.admin).patch(f"/api/checkins/{c.id}/", {"time": "18:15"}, format="json")
    assert r.status_code == 200
    assert r.json()["local_date"] == str(day) and r.json()["time"] == "6:15 PM" and r.json()["session"] == "Evening"


def test_check_in_time_cant_move_into_the_future(w):
    from apps.attendance.services import change_time, check_in
    from apps.core.errors import RuleBroken

    tz = clock.tz(w.gym)
    c = check_in(w.a, member=w.member, source="desk", at=datetime.combine(w.today, time(7), tzinfo=tz))
    with pytest.raises(RuleBroken) as e:
        change_time(c, time(9, 1), now=datetime.combine(w.today, time(9), tzinfo=tz))
    assert e.value.rule_code == "time_in_future"
    assert change_time(c, time(8, 59), now=datetime.combine(w.today, time(9), tzinfo=tz)).at.astimezone(tz).time() == time(8, 59)
    r = w.client(w.desk).patch(f"/api/checkins/{c.id}/", {"time": "7pm"}, format="json")
    assert r.status_code == 400 and "time" in r.json()["error"]["fields"]


def test_desk_removes_todays_check_in_and_can_check_in_again(w):
    from apps.attendance.services import check_in
    from apps.audit.models import AuditLog

    c = check_in(w.a, member=w.member, source="desk")
    desk = w.client(w.desk)
    assert desk.delete(f"/api/checkins/{c.id}/").status_code == 204
    assert not CheckIn.objects.filter(pk=c.id).exists()
    assert AuditLog.objects.get(action="checkin.removed").before["member"] == w.member.id
    assert desk.post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json").status_code == 201


def test_only_an_admin_corrects_an_earlier_day(w):
    from apps.attendance.services import check_in

    tz = clock.tz(w.gym)
    c = check_in(w.a, member=w.member, source="desk", at=datetime.combine(w.today - timedelta(days=1), time(7), tzinfo=tz))
    desk = w.client(w.desk)
    for r in (desk.patch(f"/api/checkins/{c.id}/", {"time": "06:00"}, format="json"), desk.delete(f"/api/checkins/{c.id}/")):
        assert r.status_code == 409 and r.json()["error"]["code"] == "past_day"
    admin = w.client(w.admin)
    assert admin.patch(f"/api/checkins/{c.id}/", {"time": "06:00"}, format="json").status_code == 200
    assert admin.delete(f"/api/checkins/{c.id}/").status_code == 204


def test_check_in_corrections_are_for_the_desk_of_its_branch_and_gym(w, other):
    from apps.attendance.services import check_in

    c = check_in(w.a, member=w.member, source="desk")
    for who in (w.client(w.trainer), w.member_client()):
        assert who.patch(f"/api/checkins/{c.id}/", {"time": "00:00"}, format="json").status_code == 403
        assert who.delete(f"/api/checkins/{c.id}/").status_code == 403
    for who in (w.client(w.desk_b), other.client(other.admin)):  # another branch's desk, another gym
        assert who.patch(f"/api/checkins/{c.id}/", {"time": "00:00"}, format="json").status_code == 404
        assert who.delete(f"/api/checkins/{c.id}/").status_code == 404
    assert w.client(w.desk).put(f"/api/checkins/{c.id}/", {"time": "00:00"}, format="json").status_code == 405
    assert CheckIn.objects.filter(pk=c.id).exists()
