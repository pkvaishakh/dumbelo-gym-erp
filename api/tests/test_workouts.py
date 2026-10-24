"""Workout plans: written by trainers and admins for the whole gym, given to members, who see their own."""
from apps.audit.models import AuditLog
from apps.workouts.models import WorkoutAssignment, WorkoutPlan

PLANS, GIVEN = "/api/workout-plans/", "/api/workout-assignments/"

PUSH = {"title": "Day 1: Push", "body_parts": ["chest", "Triceps"], "exercises": [
    {"name": " Bench  Press ", "sets": 4, "reps": "8", "load": "50 kg"},
    {"name": "Dips", "sets": 3, "reps": "10-12", "load": "Bodyweight"},
]}
PULL = {"title": "Day 2: Pull", "exercises": [{"name": "Lat Pulldown", "sets": 3, "reps": "12"}]}


def ok(r, code=200):
    assert r.status_code == code, r.content
    return r.json()


def broken(r, code):
    assert r.status_code == 409, r.content
    assert r.json()["error"]["code"] == code, r.json()


def write_plan(w, by=None, name="Beginner strength", days=(PUSH, PULL)):
    return ok(w.client(by or w.trainer).post(PLANS, {"name": name, "goal": "First 3 months", "days": list(days)}, format="json"), 201)


# ---- plans ----

def test_a_trainer_writes_a_plan_for_the_gym(w):
    p = write_plan(w)
    assert (p["name"], p["created_by_name"], p["members_count"], p["can_change"]) == ("Beginner strength", "Trainer0", 0, True)
    day = p["days"][0]
    assert day["body_parts"] == ["Chest", "Triceps"]
    assert day["exercises"][0] == {"name": "Bench Press", "sets": 4, "reps": "8", "load": "50 kg"}
    assert p["days"][1]["exercises"][0] == {"name": "Lat Pulldown", "sets": 3, "reps": "12", "load": ""}


def test_every_trainer_sees_every_plan_and_only_its_author_or_an_admin_changes_it(w):
    p = write_plan(w)
    other_trainer = w.role("arjun@x.in", "trainer", [w.b])
    seen = ok(w.client(other_trainer).get(PLANS))["results"]
    assert [(x["name"], x["can_change"]) for x in seen] == [("Beginner strength", False)]
    broken(w.client(other_trainer).patch(f"{PLANS}{p['id']}/", {"name": "Mine now"}, format="json"), "not_yours")
    assert ok(w.client(w.admin).patch(f"{PLANS}{p['id']}/", {"name": "Strength 1"}, format="json"))["name"] == "Strength 1"
    assert ok(w.client(w.trainer).patch(f"{PLANS}{p['id']}/", {"is_active": False}, format="json"))["is_active"] is False
    assert ok(w.client(other_trainer).get(PLANS))["count"] == 0  # archived plans sit apart
    assert ok(w.client(other_trainer).get(PLANS, {"archived": "true"}))["count"] == 1


def test_who_writes_and_reads_plans(w, other):
    p = write_plan(w)
    assert ok(w.client(w.desk).get(PLANS))["count"] == 1  # the desk reads them
    assert w.client(w.desk).post(PLANS, {"name": "X", "days": [PUSH]}, format="json").status_code == 403
    assert w.member_client().get(PLANS).status_code == 403
    assert other.client(other.admin).get(f"{PLANS}{p['id']}/").status_code == 404
    assert ok(other.client(other.admin).get(PLANS))["count"] == 0
    assert w.client(w.admin).put(f"{PLANS}{p['id']}/", {"name": "X", "days": [PUSH]}, format="json").status_code == 405
    assert w.client(w.admin).delete(f"{PLANS}{p['id']}/").status_code == 405


def test_a_plan_needs_days_with_exercises(w):
    for days, field in (([], "days"), ([{"title": "Day 1", "exercises": []}], "days"), ([{"title": "Day 1", "exercises": [{"name": "Squat", "sets": 0}]}], "days")):
        r = w.client(w.trainer).post(PLANS, {"name": "Bad", "days": days}, format="json")
        assert r.status_code == 400 and field in r.json()["error"]["fields"], days


def test_plans_search_and_mine(w):
    write_plan(w, name="Fat loss")
    write_plan(w, by=w.admin, name="Strength")
    assert [p["name"] for p in ok(w.client(w.trainer).get(PLANS, {"q": "fat"}))["results"]] == ["Fat loss"]
    assert [p["name"] for p in ok(w.client(w.trainer).get(PLANS, {"mine": "true"}))["results"]] == ["Fat loss"]


# ---- giving plans to members ----

def test_a_trainer_gives_their_member_a_plan_and_the_member_sees_it(w):
    p = write_plan(w)
    a = ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id, "note": " Start light "}, format="json"), 201)
    assert (a["plan_name"], a["member_name"], a["assigned_by_name"], a["note"], a["current"]) == ("Beginner strength", "Asha", "Trainer0", "Start light", True)
    mine = ok(w.member_client().get(GIVEN, {"current": "true"}))["results"]
    assert [m["plan_name"] for m in mine] == ["Beginner strength"]
    assert mine[0]["days"][0]["exercises"][0]["name"] == "Bench Press"
    assert ok(w.client(w.trainer).get(f"{PLANS}{p['id']}/"))["members_count"] == 1
    assert AuditLog.objects.filter(action="workout.assigned").count() == 1


def test_a_new_plan_ends_the_one_they_were_on(w):
    first, second = write_plan(w, name="A"), write_plan(w, name="B")
    ok(w.client(w.trainer).post(GIVEN, {"plan": first["id"], "member": w.member.id}, format="json"), 201)
    broken(w.client(w.trainer).post(GIVEN, {"plan": first["id"], "member": w.member.id}, format="json"), "already_assigned")
    ok(w.client(w.trainer).post(GIVEN, {"plan": second["id"], "member": w.member.id}, format="json"), 201)
    rows = ok(w.client(w.trainer).get(GIVEN, {"member": w.member.id}))["results"]
    assert [(r["plan_name"], r["current"]) for r in rows] == [("B", True), ("A", False)]  # history stays
    assert WorkoutAssignment.objects.filter(member=w.member, ended_at__isnull=True).count() == 1


def test_an_archived_plan_isnt_given(w):
    p = write_plan(w)
    WorkoutPlan.objects.filter(pk=p["id"]).update(is_active=False)
    broken(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), "archived")


def test_who_gives_plans_to_whom(w, other):
    p = write_plan(w)
    stranger = w.role("arjun@x.in", "trainer", [w.a])  # not Asha's trainer
    r = w.client(stranger).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json")
    assert r.status_code == 400 and "member" in r.json()["error"]["fields"]
    assert w.client(w.desk).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json").status_code == 403
    assert w.member_client().post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json").status_code == 403
    r = other.client(other.admin).post(GIVEN, {"plan": p["id"], "member": other.member.id}, format="json")
    assert r.status_code == 400 and "plan" in r.json()["error"]["fields"]  # another gym's plan
    ok(w.client(w.admin).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), 201)  # admins give anyone


def test_who_sees_which_plans_members_are_on(w, other):
    p = write_plan(w)
    ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), 201)
    assert ok(w.client(w.desk).get(GIVEN))["count"] == 1
    assert ok(w.client(w.desk_b).get(GIVEN))["count"] == 0  # another branch's member
    assert ok(w.client(w.role("arjun@x.in", "trainer", [w.a])).get(GIVEN))["count"] == 0
    assert ok(other.client(other.admin).get(GIVEN))["count"] == 0


def test_taking_a_member_off_their_plan(w):
    p = write_plan(w)
    a = ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), 201)
    assert w.member_client().post(f"{GIVEN}{a['id']}/end/").status_code == 403
    assert ok(w.client(w.trainer).post(f"{GIVEN}{a['id']}/end/"))["current"] is False
    broken(w.client(w.trainer).post(f"{GIVEN}{a['id']}/end/"), "ended")
    assert ok(w.member_client().get(GIVEN, {"current": "true"}))["count"] == 0
    assert AuditLog.objects.filter(action="workout.ended").count() == 1


# ---- queries ----

def test_lists_cost_the_same_for_more_plans(w, django_assert_max_num_queries):
    def grow(n):
        for i in range(n):
            p = write_plan(w, name=f"Plan {WorkoutPlan.objects.count()}")
            m = w.new_member(f"M {i}", f"97{7000 + WorkoutPlan.objects.count():08d}", w.a, trainer=w.trainer)
            ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": m.id}, format="json"), 201)

    grow(6)
    for url in (PLANS, GIVEN):
        with django_assert_max_num_queries(8):
            ok(w.client(w.trainer).get(url))


# ---- members by plan ----

def test_members_filter_by_workout_and_diet_plan(w, django_assert_max_num_queries):
    from apps.members.services import sell

    a, b = write_plan(w, name="A"), write_plan(w, name="B")
    diet = ok(w.client(w.trainer).post("/api/diet-plans/", {"name": "D", "meals": [{"name": "Lunch", "food": "Dal rice"}]}, format="json"), 201)
    ravi = w.new_member("Ravi", "9800000099", w.a, trainer=w.trainer)
    sell(ravi, w.monthly, by=w.desk, starts=w.today)
    w.new_member("Zoya", "9800000098", w.a, trainer=w.trainer)  # on no plan
    for plan, member in ((a, w.member), (b, ravi)):
        ok(w.client(w.trainer).post(GIVEN, {"plan": plan["id"], "member": member.id}, format="json"), 201)
    ok(w.client(w.trainer).post("/api/diet-assignments/", {"plan": diet["id"], "member": w.member.id}, format="json"), 201)

    def names(**params):
        return [m["name"] for m in ok(w.client(w.trainer).get("/api/members/", params))["results"]]

    assert names(workout=a["id"]) == ["Asha"]
    assert names(workout="any") == ["Asha", "Ravi"]
    assert names(workout="none") == ["Zoya"]
    assert names(diet="none") == ["Ravi", "Zoya"]
    assert names(workout="any", diet=diet["id"]) == ["Asha"]
    assert names(workout="any", status="due") == ["Ravi"]  # the status path keeps the filter; Ravi has yet to pay
    # A plan someone has left no longer finds them.
    ok(w.client(w.trainer).post(GIVEN, {"plan": b["id"], "member": w.member.id}, format="json"), 201)
    assert names(workout=a["id"]) == []
    r = w.client(w.trainer).get("/api/members/", {"workout": "abc"})
    assert r.status_code == 400 and "workout" in r.json()["error"]["fields"]
    with django_assert_max_num_queries(8):
        ok(w.client(w.desk).get("/api/members/", {"workout": "any", "diet": "none"}))
