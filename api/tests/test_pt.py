"""Personal training: sold on top of a membership or alone (the gym's choice), its sessions counted as they are given."""
from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.audit.models import AuditLog
from apps.members.models import Plan, PTSession
from apps.members.services import mark_session, sell

SUBS, SESSIONS, SETTINGS = "/api/subscriptions/", "/api/pt-sessions/", "/api/gym/settings/"


def pt_plan(w, sessions=3, months=3):
    return Plan.objects.create(gym=w.gym, name=f"PT {sessions}", kind=Plan.PT, months=months, sessions=sessions, price_paise=600000)


def pt_only(w):
    w.gym.pt_needs_membership = False
    w.gym.save(update_fields=["pt_needs_membership"])


def ok(r, code=200):
    assert r.status_code == code, r.content
    return r.json()


def broken(r, code):
    assert r.status_code == 409, r.content
    assert r.json()["error"]["code"] == code, r.json()


def sell_pt(w, member, plan, by=None, **body):
    return w.client(by or w.desk).post(SUBS, {"member": member.id, "plan": plan.id, **body}, format="json")


# ---- selling ----

def test_pt_on_top_of_a_membership_starts_today_with_its_sessions_and_trainer(w):
    pt = pt_plan(w, sessions=12)
    other_trainer = w.role("arjun@x.in", "trainer", [w.a])
    sub = ok(sell_pt(w, w.member, pt, trainer=other_trainer.id), 201)
    # It runs beside the membership, not after it.
    assert sub["starts"] == str(w.today)
    assert (sub["kind"], sub["sessions"], sub["sessions_used"], sub["trainer_name"]) == ("pt", 12, 0, "Arjun")
    w.member.refresh_from_db()
    assert w.member.trainer_id == other_trainer.id  # they become the member's trainer
    m = ok(w.client(w.desk).get(f"/api/members/{w.member.id}/"))
    assert m["plan"]["kind"] == "membership" and m["status"] == "due"  # the PT isn't paid for yet
    assert {k: m["pt"][k] for k in ("id", "sessions", "sessions_used", "trainer_name")} == {"id": sub["id"], "sessions": 12, "sessions_used": 0, "trainer_name": "Arjun"}


def test_pt_without_a_trainer_given_uses_the_members_own(w):
    sub = ok(sell_pt(w, w.member, pt_plan(w)), 201)
    assert sub["trainer"] == w.trainer.id


def test_a_membership_has_no_trainer(w):
    r = w.client(w.desk).post(SUBS, {"member": w.member.id, "plan": w.monthly.id, "trainer": w.trainer.id}, format="json")
    assert r.status_code == 400 and "trainer" in r.json()["error"]["fields"]


def test_pt_needs_a_membership_on_its_first_day_by_default(w):
    new = w.new_member("Ravi", "9800000099", w.a)
    broken(sell_pt(w, new, pt_plan(w)), "membership_needed")
    # A day after the membership ends is refused too, even with one running today.
    broken(sell_pt(w, w.member, pt_plan(w, 4), starts=str(w.member.subscriptions.get().ends + timedelta(days=1))), "membership_needed")


def test_a_gym_that_sells_pt_alone_lets_it_in(w):
    pt_only(w)
    new = w.new_member("Ravi", "9800000099", w.a)
    ok(sell_pt(w, new, pt_plan(w)), 201)
    m = ok(w.client(w.desk).get(f"/api/members/{new.id}/"))
    assert m["plan"]["kind"] == "pt" and m["status"] == "due"  # nothing paid yet
    ok(w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": new.id}, format="json"), 201)


def test_new_member_with_pt_as_first_plan_follows_the_rule(w):
    body = {"name": "Ravi", "phone": "9800000099", "home_branch": w.a.id, "first_plan": pt_plan(w).id}
    broken(w.client(w.desk).post("/api/members/", body, format="json"), "membership_needed")
    pt_only(w)
    ok(w.client(w.desk).post("/api/members/", body, format="json"), 201)


# ---- who gets in ----

def test_running_pt_doesnt_let_in_a_member_whose_membership_ended(w):
    sell(w.member, pt_plan(w), by=w.desk)
    membership = w.member.subscriptions.get(plan=w.monthly)
    membership.ends = w.today - timedelta(days=1)
    membership.save(update_fields=["ends"])
    assert ok(w.client(w.desk).get(f"/api/members/{w.member.id}/"))["status"] == "expired"
    broken(w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json"), "membership_expired")
    sub = w.member.subscriptions.get(plan__kind=Plan.PT)
    broken(w.client(w.trainer).post(SESSIONS, {"subscription": sub.id}, format="json"), "membership_needed")
    # The same member at a gym that sells PT alone is let in by it.
    pt_only(w)
    assert ok(w.client(w.desk).get(f"/api/members/{w.member.id}/"))["status"] in ("active", "due", "expiring")
    ok(w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": w.member.id}, format="json"), 201)


def test_pt_alone_is_told_apart_when_the_gym_turns_the_rule_back_on(w):
    pt_only(w)
    new = w.new_member("Ravi", "9800000099", w.a)
    sell(new, pt_plan(w), by=w.desk)
    w.gym.pt_needs_membership = True
    w.gym.save(update_fields=["pt_needs_membership"])
    r = w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": new.id}, format="json")
    broken(r, "membership_expired")
    assert "no membership" in r.json()["error"]["message"]


def test_pt_with_every_session_used_has_ended(w):
    pt_only(w)
    new = w.new_member("Ravi", "9800000099", w.a, trainer=w.trainer)
    sub = sell(new, pt_plan(w, sessions=1), by=w.desk, starts=w.today - timedelta(days=1))
    mark_session(sub, by=w.trainer, on=w.today - timedelta(days=1))
    assert ok(w.client(w.desk).get(f"/api/members/{new.id}/"))["status"] == "expired"
    broken(w.client(w.desk).post("/api/checkins/", {"branch": w.a.id, "member": new.id}, format="json"), "membership_expired")


def test_pt_near_its_last_session_is_expiring(w):
    pt_only(w)
    new = w.new_member("Ravi", "9800000099", w.a, trainer=w.trainer)
    sub = sell(new, pt_plan(w, sessions=3), by=w.desk, starts=w.today - timedelta(days=1))
    sub.payments.create(gym=w.gym, member=new, branch=w.a, amount_paise=sub.price_paise, method="cash", taken_by=w.desk)
    assert ok(w.client(w.desk).get(f"/api/members/{new.id}/"))["status"] == "active"
    mark_session(sub, by=w.trainer, on=w.today - timedelta(days=1))
    assert ok(w.client(w.desk).get(f"/api/members/{new.id}/"))["status"] == "expiring"  # 2 left


# ---- marking sessions ----

def pt_for_member(w, sessions=3):
    return sell(w.member, pt_plan(w, sessions), by=w.desk, starts=w.today - timedelta(days=3))


def test_the_trainer_marks_todays_session_once(w):
    sub = pt_for_member(w)
    s = ok(w.client(w.trainer).post(SESSIONS, {"subscription": sub.id}, format="json"), 201)
    assert (s["local_date"], s["trainer_name"], s["marked_by_name"]) == (str(w.today), "Trainer0", "Trainer0")
    broken(w.client(w.desk).post(SESSIONS, {"subscription": sub.id}, format="json"), "session_already_marked")
    assert ok(w.client(w.desk).get(f"/api/members/{w.member.id}/"))["pt"]["sessions_used"] == 1
    assert AuditLog.objects.filter(action="pt_session.marked").count() == 1


def test_the_desk_marks_an_earlier_day_and_a_trainer_only_today(w):
    sub = pt_for_member(w)
    yesterday = str(w.today - timedelta(days=1))
    r = w.client(w.trainer).post(SESSIONS, {"subscription": sub.id, "local_date": yesterday}, format="json")
    assert r.status_code == 400 and "local_date" in r.json()["error"]["fields"]
    s = ok(w.client(w.desk).post(SESSIONS, {"subscription": sub.id, "local_date": yesterday}, format="json"), 201)
    assert s["trainer_name"] == "Trainer0"  # the plan's trainer, though the desk marked it
    broken(w.client(w.desk).post(SESSIONS, {"subscription": sub.id, "local_date": str(w.today + timedelta(days=1))}, format="json"), "day_in_future")
    broken(w.client(w.desk).post(SESSIONS, {"subscription": sub.id, "local_date": str(w.today - timedelta(days=9))}, format="json"), "outside_plan")


def test_no_session_past_the_last_one(w):
    sub = pt_for_member(w, sessions=1)
    ok(w.client(w.trainer).post(SESSIONS, {"subscription": sub.id}, format="json"), 201)
    broken(w.client(w.desk).post(SESSIONS, {"subscription": sub.id, "local_date": str(w.today - timedelta(days=1))}, format="json"), "no_sessions_left")


def test_sessions_are_marked_on_personal_training_only(w):
    membership = w.member.subscriptions.get()
    broken(w.client(w.desk).post(SESSIONS, {"subscription": membership.id}, format="json"), "not_pt")


def test_who_may_mark_whose_session(w, other):
    sub = pt_for_member(w)
    stranger = w.role("arjun@x.in", "trainer", [w.a])
    for c in (w.client(stranger), w.client(w.desk_b)):  # not their member, not their branch
        assert c.post(SESSIONS, {"subscription": sub.id}, format="json").status_code == 400
    assert w.member_client().post(SESSIONS, {"subscription": sub.id}, format="json").status_code == 403
    assert other.client(other.admin).post(SESSIONS, {"subscription": sub.id}, format="json").status_code == 400  # another gym's plan


def test_who_sees_which_sessions(w, other):
    sub = pt_for_member(w)
    mark_session(sub, by=w.trainer)
    assert ok(w.client(w.trainer).get(SESSIONS))["count"] == 1
    assert ok(w.member_client().get(SESSIONS))["count"] == 1
    assert ok(w.client(w.desk).get(SESSIONS, {"member": w.member.id}))["count"] == 1
    assert ok(w.client(w.desk_b).get(SESSIONS))["count"] == 0
    assert ok(w.client(w.role("arjun@x.in", "trainer", [w.a])).get(SESSIONS))["count"] == 0
    assert ok(other.client(other.admin).get(SESSIONS))["count"] == 0


def test_a_session_marked_by_mistake_is_removed_never_deleted(w):
    sub = pt_for_member(w)
    s = mark_session(sub, by=w.trainer)
    broken(w.client(w.desk).post(f"{SESSIONS}{s.id}/void/", {"reason": "Wrong member"}, format="json"), "not_yours")
    r = ok(w.client(w.trainer).post(f"{SESSIONS}{s.id}/void/", {"reason": "Wrong member"}, format="json"))
    assert r["voided"] and r["void_reason"] == "Wrong member"
    assert PTSession.objects.filter(pk=s.pk).exists()
    assert ok(w.client(w.desk).get(f"/api/members/{w.member.id}/"))["pt"]["sessions_used"] == 0
    broken(w.client(w.admin).post(f"{SESSIONS}{s.id}/void/", {"reason": "Again"}, format="json"), "voided")
    # Today's session can be marked again, and an admin removes any.
    s2 = ok(w.client(w.trainer).post(SESSIONS, {"subscription": sub.id}, format="json"), 201)
    ok(w.client(w.admin).post(f"{SESSIONS}{s2['id']}/void/", {"reason": "Cancelled"}, format="json"))
    assert AuditLog.objects.filter(action="pt_session.voided").count() == 2


def test_a_session_says_what_they_worked_and_its_notes_can_change(w):
    sub = pt_for_member(w)
    body = {"subscription": sub.id, "body_parts": ["chest", "Triceps", " Core  work ", "CHEST"], "notes": " Bench 40 kg x 8 "}
    s = ok(w.client(w.trainer).post(SESSIONS, body, format="json"), 201)
    # The usual parts are spelt one way; any other is kept as typed, each once.
    assert (s["body_parts"], s["notes"]) == (["Chest", "Triceps", "Core work"], "Bench 40 kg x 8")
    r = ok(w.client(w.desk).patch(f"{SESSIONS}{s['id']}/", {"body_parts": ["Legs", "Cardio"]}, format="json"))
    assert (r["body_parts"], r["notes"]) == (["Legs", "Cardio"], "Bench 40 kg x 8")  # what's left out stays
    r = ok(w.client(w.trainer).patch(f"{SESSIONS}{s['id']}/", {"notes": ""}, format="json"))
    assert (r["body_parts"], r["notes"], r["local_date"]) == (["Legs", "Cardio"], "", str(w.today))
    log = AuditLog.objects.filter(action="pt_session.updated").first()
    assert (log.before, log.after) == ({"body_parts": ["Legs", "Cardio"], "notes": "Bench 40 kg x 8"}, {"body_parts": ["Legs", "Cardio"], "notes": ""})
    assert ok(w.member_client().get(f"{SESSIONS}{s['id']}/"))["body_parts"] == ["Legs", "Cardio"]  # the member sees it


def test_a_session_marked_without_body_parts_has_none(w):
    s = ok(w.client(w.trainer).post(SESSIONS, {"subscription": pt_for_member(w).id}, format="json"), 201)
    assert (s["body_parts"], s["notes"]) == ([], "")


def test_body_parts_are_short_and_few(w):
    sub = pt_for_member(w)
    for parts in (["x" * 31], [""], [f"Part {i}" for i in range(13)]):
        r = w.client(w.trainer).post(SESSIONS, {"subscription": sub.id, "body_parts": parts}, format="json")
        assert r.status_code == 400 and "body_parts" in r.json()["error"]["fields"], parts


def test_who_may_change_a_sessions_notes(w, other):
    s = mark_session(pt_for_member(w), by=w.trainer)
    url = f"{SESSIONS}{s.id}/"
    assert w.member_client().patch(url, {"notes": "Easy"}, format="json").status_code == 403
    for c in (w.client(w.role("arjun@x.in", "trainer", [w.a])), w.client(w.desk_b), other.client(other.admin)):
        assert c.patch(url, {"notes": "Easy"}, format="json").status_code == 404
    assert w.client(w.admin).put(url, {"notes": "Easy"}, format="json").status_code == 405
    ok(w.client(w.trainer).post(f"{url}void/", {"reason": "Wrong member"}, format="json"))
    broken(w.client(w.trainer).patch(url, {"notes": "Easy"}, format="json"), "voided")


def test_a_trainer_cant_remove_yesterdays_session(w):
    sub = pt_for_member(w)
    s = mark_session(sub, by=w.trainer, on=w.today - timedelta(days=1))
    PTSession.objects.filter(pk=s.pk).update(marked_at=s.marked_at - timedelta(days=1))
    broken(w.client(w.trainer).post(f"{SESSIONS}{s.id}/void/", {"reason": "Oops"}, format="json"), "not_yours")


# ---- correcting, settings, queries ----

def test_correcting_pt_keeps_the_sessions_already_given(w):
    sub = pt_for_member(w, sessions=3)
    mark_session(sub, by=w.trainer, on=w.today - timedelta(days=1))
    mark_session(sub, by=w.trainer)
    smaller = pt_plan(w, sessions=1)
    r = w.client(w.admin).post(f"{SUBS}{sub.id}/correct/", {"plan": smaller.id, "reason": "Wrong pack"}, format="json")
    broken(r, "sessions_below_used")
    bigger = pt_plan(w, sessions=8)
    ok(w.client(w.admin).post(f"{SUBS}{sub.id}/correct/", {"plan": bigger.id, "reason": "Wrong pack", "starts": str(sub.starts)}, format="json"))
    sub.refresh_from_db()
    assert sub.sessions == 8


def test_admins_choose_whether_pt_needs_a_membership(w):
    assert ok(w.client(w.desk).get("/api/me/"))["roles"][0]["pt_needs_membership"] is True
    assert ok(w.client(w.admin).patch(SETTINGS, {"pt_needs_membership": False}, format="json"))["pt_needs_membership"] is False
    log = AuditLog.objects.get(action="gym.settings_changed")
    assert (log.before, log.after) == ({"pt_needs_membership": True}, {"pt_needs_membership": False})
    assert w.client(w.desk).patch(SETTINGS, {"pt_needs_membership": True}, format="json").status_code == 403


def test_the_trainer_sees_sessions_but_no_amounts(w):
    pt_for_member(w)
    m = ok(w.client(w.trainer).get(f"/api/members/{w.member.id}/"))
    assert m["pt"]["sessions"] == 3 and "balance_paise" not in m and "price_paise" not in m["pt"]


def count(client, url, params=None):
    with CaptureQueriesContext(connection) as q:
        ok(client.get(url, params))
    return len(q.captured_queries)


def test_lists_cost_the_same_for_more_pt(w):
    pt = pt_plan(w, sessions=10)

    def grow(n):
        for _ in range(n):
            i = PTSession.objects.count()
            m = w.new_member(f"PT {i}", f"97{6000 + i:08d}", w.a, trainer=w.trainer)
            sell(m, w.monthly, by=w.desk, starts=w.today - timedelta(days=3))
            mark_session(sell(m, pt, by=w.desk, starts=w.today - timedelta(days=3)), by=w.trainer)

    lists = [(w.desk, SESSIONS, None), (w.desk, "/api/members/", None), (w.desk, "/api/members/", {"status": "active"}), (w.desk, SUBS, None),
             (w.trainer, "/api/members/", None), (w.trainer, SESSIONS, None)]
    grow(2)
    few = [count(w.client(who), u, p) for who, u, p in lists]
    grow(5)
    assert [count(w.client(who), u, p) for who, u, p in lists] == few
