"""Diet plans: written by trainers and admins for the whole gym, given to members, who see their own. They follow
the workout plans' rules (tests/test_workouts.py), so this covers what's their own and that the rules hold."""
from apps.audit.models import AuditLog
from apps.workouts.models import DietPlan

PLANS, GIVEN = "/api/diet-plans/", "/api/diet-assignments/"
MEALS = [
    {"name": "Breakfast", "time": "7:30 AM", "food": " Oats with banana and milk ", "kcal": 450},
    {"name": "Lunch", "food": "2 rotis, dal, grilled chicken or paneer, salad", "kcal": 650},
    {"name": "Dinner", "time": "8 PM", "food": "Brown rice, fish curry, vegetables"},
]


def ok(r, code=200):
    assert r.status_code == code, r.content
    return r.json()


def broken(r, code):
    assert r.status_code == 409, r.content
    assert r.json()["error"]["code"] == code, r.json()


def write_diet(w, by=None, name="Lean 2000", meals=MEALS):
    body = {"name": name, "goal": "Fat loss", "kcal": 2000, "protein_g": 140, "carbs_g": 200, "fat_g": 60, "meals": meals}
    return ok(w.client(by or w.trainer).post(PLANS, body, format="json"), 201)


def test_a_trainer_writes_a_diet_and_gives_it_to_their_member(w):
    p = write_diet(w)
    assert (p["kcal"], p["protein_g"], p["created_by_name"], p["can_change"], p["members_count"]) == (2000, 140, "Trainer0", True, 0)
    assert p["meals"][0] == {"name": "Breakfast", "time": "7:30 AM", "food": "Oats with banana and milk", "kcal": 450}
    assert p["meals"][2]["kcal"] is None
    a = ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id, "note": "Water: 3 litres"}, format="json"), 201)
    assert (a["plan_name"], a["kcal"], a["note"], a["current"]) == ("Lean 2000", 2000, "Water: 3 litres", True)
    mine = ok(w.member_client().get(GIVEN, {"current": "true"}))["results"]
    assert [m["meals"][1]["name"] for m in mine] == ["Lunch"]
    assert AuditLog.objects.filter(action="diet.assigned").count() == 1


def test_a_diet_needs_meals_with_food_and_sensible_targets(w):
    for body, field in (({"meals": []}, "meals"), ({"meals": [{"name": "Lunch", "food": ""}]}, "meals"), ({"meals": MEALS, "kcal": 100}, "kcal")):
        r = w.client(w.trainer).post(PLANS, {"name": "Bad", **body}, format="json")
        assert r.status_code == 400 and field in r.json()["error"]["fields"], body


def test_only_its_author_or_an_admin_changes_a_diet(w):
    p = write_diet(w)
    other_trainer = w.role("arjun@x.in", "trainer", [w.b])
    assert ok(w.client(other_trainer).get(f"{PLANS}{p['id']}/"))["can_change"] is False
    broken(w.client(other_trainer).patch(f"{PLANS}{p['id']}/", {"kcal": 2500}, format="json"), "not_yours")
    assert ok(w.client(w.admin).patch(f"{PLANS}{p['id']}/", {"kcal": 2200}, format="json"))["kcal"] == 2200


def test_a_member_has_one_diet_and_one_workout_plan(w):
    first, second = write_diet(w, name="A"), write_diet(w, name="B")
    ok(w.client(w.trainer).post(GIVEN, {"plan": first["id"], "member": w.member.id}, format="json"), 201)
    ok(w.client(w.trainer).post(GIVEN, {"plan": second["id"], "member": w.member.id}, format="json"), 201)
    rows = ok(w.client(w.trainer).get(GIVEN, {"member": w.member.id}))["results"]
    assert [(r["plan_name"], r["current"]) for r in rows] == [("B", True), ("A", False)]
    # A workout plan is its own: giving one leaves the diet alone.
    workout = ok(w.client(w.trainer).post("/api/workout-plans/", {"name": "W", "days": [{"title": "Day 1", "exercises": [{"name": "Squat"}]}]}, format="json"), 201)
    ok(w.client(w.trainer).post("/api/workout-assignments/", {"plan": workout["id"], "member": w.member.id}, format="json"), 201)
    assert ok(w.client(w.trainer).get(GIVEN, {"member": w.member.id, "current": "true"}))["count"] == 1
    # And a workout plan's id isn't a diet plan.
    r = w.client(w.trainer).post(GIVEN, {"plan": workout["id"] + 1000, "member": w.member.id}, format="json")
    assert r.status_code == 400 and "plan" in r.json()["error"]["fields"]


def test_who_writes_gives_and_sees_diets(w, other):
    p = write_diet(w)
    assert ok(w.client(w.desk).get(PLANS))["count"] == 1
    assert w.client(w.desk).post(PLANS, {"name": "X", "meals": MEALS}, format="json").status_code == 403
    assert w.member_client().get(PLANS).status_code == 403
    assert other.client(other.admin).get(f"{PLANS}{p['id']}/").status_code == 404
    stranger = w.role("arjun@x.in", "trainer", [w.a])
    r = w.client(stranger).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json")
    assert r.status_code == 400 and "member" in r.json()["error"]["fields"]
    ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), 201)
    assert ok(w.client(w.desk).get(GIVEN))["count"] == 1
    assert ok(w.client(w.desk_b).get(GIVEN))["count"] == 0
    assert ok(other.client(other.admin).get(GIVEN))["count"] == 0


def test_an_archived_diet_isnt_given_and_one_ends(w):
    p = write_diet(w)
    a = ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), 201)
    assert ok(w.client(w.trainer).post(f"{GIVEN}{a['id']}/end/"))["current"] is False
    DietPlan.objects.filter(pk=p["id"]).update(is_active=False)
    broken(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": w.member.id}, format="json"), "archived")


def test_diet_lists_cost_the_same_for_more_plans(w, django_assert_max_num_queries):
    for i in range(6):
        p = write_diet(w, name=f"Diet {i}")
        m = w.new_member(f"M {i}", f"97{8000 + i:08d}", w.a, trainer=w.trainer)
        ok(w.client(w.trainer).post(GIVEN, {"plan": p["id"], "member": m.id}, format="json"), 201)
    for url in (PLANS, GIVEN):
        with django_assert_max_num_queries(8):
            ok(w.client(w.trainer).get(url))
