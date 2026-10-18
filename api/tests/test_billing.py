"""A gym's Rackline plan: price lists, the branch quota, asking for more branches and what approving one costs."""
import importlib
import threading
import time
from datetime import date, timedelta

import pytest
from django.apps import apps as django_apps
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.billing import services
from apps.billing.models import BranchRequest, GymBilling, PriceList
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.gyms.models import Branch, Gym, GymRole
from apps.platform.services import create_gym
from tests.conftest import PRICES, World

PLAN = "/api/billing/plan/"
ASKS = "/api/billing/branch-requests/"
PRICE_LISTS = "/api/platform/prices/"
CONSOLE_ASKS = "/api/platform/branch-requests/"
BRANCH = {"sessions": [{"name": "Morning", "starts": "06:00", "ends": "10:00"}]}


def rackline(email="ops@rackline.in"):
    user = User.objects.create_superuser(email=email, password="pass12345", name="Rackline Ops")
    c = APIClient()
    c.force_authenticate(user)
    return c


def console_plan(gym):
    return f"/api/platform/gyms/{gym.id}/plan/"


def new_branch(c, name):
    return c.post("/api/branches/", {"name": name, **BRANCH}, format="json")


def ask(w, count=1, note=""):
    r = w.client(w.admin).post(ASKS, {"count": count, "note": note}, format="json")
    assert r.status_code == 201, r.content
    return r.json()


# The quota

def test_a_branch_past_the_quota_is_refused(w):
    c = w.client(w.admin)
    r = new_branch(c, "C")
    assert r.status_code == 409
    assert r.json()["error"] == {"code": "branch_limit", "message": "Your plan has room for 2 branches. Ask for another one to open this branch."}
    assert not Branch.objects.filter(gym=w.gym, name="C").exists()
    assert new_branch(c, "C").json()["error"]["code"] == "branch_limit"  # nothing half-made the first time
    # A closed branch can be added: it takes no place until it opens.
    assert c.post("/api/branches/", {"name": "D", "is_active": False, **BRANCH}, format="json").status_code == 201


def test_a_plan_for_one_branch_says_so(w):
    Branch.objects.filter(pk=w.b.pk).update(is_active=False)
    GymBilling.objects.filter(gym=w.gym).update(branch_quota=1)
    assert new_branch(w.client(w.admin), "C").json()["error"]["message"].startswith("Your plan has room for 1 branch.")


def test_reopening_a_branch_past_the_quota_is_refused(w):
    c = w.client(w.admin)
    assert c.patch(f"/api/branches/{w.b.id}/", {"is_active": False}, format="json").status_code == 200
    assert new_branch(c, "C").status_code == 201  # B's place went to C
    r = c.patch(f"/api/branches/{w.b.id}/", {"is_active": True}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "branch_limit"
    w.b.refresh_from_db()
    assert not w.b.is_active
    # Saving an open branch's other details never counts it twice.
    assert c.patch(f"/api/branches/{w.a.id}/", {"name": "A North", "is_active": True}, format="json").status_code == 200


def _overlap(first, second):
    """`first` holds its transaction open a moment after it's done; `second` runs while it's open."""
    started, out = threading.Event(), {}

    def run(name, fn, hold):
        try:
            with transaction.atomic():
                out[name] = fn()
                if hold:
                    started.set()
                    time.sleep(0.3)
        except RuleBroken as e:
            out[name] = e.rule_code
        finally:
            started.set()
            connection.close()

    one = threading.Thread(target=run, args=("first", first, True))
    two = threading.Thread(target=lambda: (started.wait(), run("second", second, False)))
    for t in (one, two):
        t.start()
    for t in (one, two):
        t.join()
    return out["first"], out["second"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_two_branches_opened_at_once_cant_both_take_the_last_place():
    w = World("race")
    GymBilling.objects.filter(gym=w.gym).update(branch_quota=3)

    def open_branch(name):
        def go():
            services.make_room_for_branch(w.gym)
            return Branch.objects.create(gym=w.gym, name=name).name
        return go

    assert _overlap(open_branch("C"), open_branch("D")) == ("C", "branch_limit")
    assert Branch.objects.filter(gym=w.gym, is_active=True).count() == 3


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_a_quota_lowered_while_a_branch_opens_never_ends_up_below_it():
    w = World("race")
    GymBilling.objects.filter(gym=w.gym).update(branch_quota=3)

    def open_c():
        services.make_room_for_branch(w.gym)
        return Branch.objects.create(gym=w.gym, name="C").name

    assert _overlap(open_c, lambda: services.change_plan(w.gym, branch_quota=2)) == ("C", "below_branches")
    assert GymBilling.objects.get(gym=w.gym).branch_quota == 3


# The Console sets the plan

def test_console_shows_and_changes_a_gyms_plan(w):
    c = rackline()
    plan = c.get(console_plan(w.gym)).json()
    assert plan["branch_quota"] == 2 and plan["branches_in_use"] == 2 and plan["billing_day"] == 1
    assert plan["whatsapp_mode"] == "shared" and plan["paid_until"] is None and plan["current_prices"] is None
    assert plan["monthly_paise"] == PRICES["base_paise"] + 2 * PRICES["per_branch_paise"]
    assert plan["per_branch_paise"] == PRICES["per_branch_paise"]

    r = c.patch(console_plan(w.gym), {"branch_quota": 4, "billing_day": 15, "whatsapp_mode": "off"}, format="json")
    assert r.status_code == 200
    assert (r.json()["branch_quota"], r.json()["billing_day"], r.json()["whatsapp_mode"]) == (4, 15, "off")
    row = AuditLog.objects.get(action="billing.changed")
    assert row.gym == w.gym and row.before["branch_quota"] == 2 and row.after == {"branch_quota": 4, "billing_day": 15, "whatsapp_mode": "off"}
    c.patch(console_plan(w.gym), {"billing_day": 15}, format="json")
    assert AuditLog.objects.filter(action="billing.changed").count() == 1  # nothing changed, nothing written


def test_a_quota_is_never_lowered_below_the_branches_open(w):
    c = rackline()
    r = c.patch(console_plan(w.gym), {"branch_quota": 1}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "below_branches"
    assert r.json()["error"]["message"] == f"{w.gym.name} has 2 branches open. Its plan can't have room for fewer."
    Branch.objects.filter(pk=w.b.pk).update(is_active=False)
    assert c.patch(console_plan(w.gym), {"branch_quota": 1}, format="json").json()["branch_quota"] == 1


@pytest.mark.parametrize("body", [{"branch_quota": 0}, {"billing_day": 29}, {"billing_day": 0}, {"whatsapp_mode": "sms"}])
def test_plan_changes_are_checked(w, body):
    r = rackline().patch(console_plan(w.gym), body, format="json")
    assert r.status_code == 400 and list(body)[0] in r.json()["error"]["fields"]


def test_only_rackline_admins_reach_billing_in_the_console(w):
    for c in (w.client(w.admin), w.client(w.desk), w.member_client()):
        assert c.get(PRICE_LISTS).status_code == 403
        assert c.post(PRICE_LISTS, {}, format="json").status_code == 403
        assert c.get(console_plan(w.gym)).status_code == 403
        assert c.patch(console_plan(w.gym), {"branch_quota": 9}, format="json").status_code == 403
        assert c.post(f"{console_plan(w.gym)}current-prices/").status_code == 403
        assert c.get(CONSOLE_ASKS).status_code == 403
    assert rackline().get("/api/platform/gyms/99999/plan/").status_code == 404


# Price lists

def price_body(active_from, **change):
    return {"active_from": active_from.isoformat(), **PRICES, **change}


def test_price_lists_are_added_never_edited(w, other, django_assert_max_num_queries):
    c = rackline()
    today = timezone.localdate()
    r = c.post(PRICE_LISTS, price_body(today, per_branch_paise=3_500_00, note="Diwali 2026"), format="json")
    assert r.status_code == 201, r.content
    new = r.json()
    assert new["is_current"] is True and new["gym_count"] == 0 and new["per_branch_paise"] == 3_500_00
    assert AuditLog.objects.get(action="price_list.added").gym is None  # Rackline's own, not a gym's
    later = c.post(PRICE_LISTS, price_body(today + timedelta(days=30)), format="json").json()
    assert later["is_current"] is False  # it starts later

    with django_assert_max_num_queries(4):
        rows = c.get(PRICE_LISTS).json()["results"]
    assert [x["id"] for x in rows] == [later["id"], new["id"], PriceList.objects.get(active_from=date(2026, 1, 1)).id]
    assert rows[2]["gym_count"] == 2 and rows[2]["is_current"] is False  # both gyms are still on the old prices

    assert c.patch(f"{PRICE_LISTS}{new['id']}/", {"base_paise": 1}, format="json").status_code in (404, 405)
    assert c.delete(f"{PRICE_LISTS}{new['id']}/").status_code in (404, 405)


def test_price_list_errors(w):
    c = rackline()
    today = timezone.localdate()
    assert c.post(PRICE_LISTS, price_body(today - timedelta(days=1)), format="json").json()["error"]["code"] == "past_date"
    assert c.post(PRICE_LISTS, price_body(today), format="json").status_code == 201
    assert c.post(PRICE_LISTS, price_body(today), format="json").json()["error"]["code"] == "date_taken"
    r = c.post(PRICE_LISTS, price_body(today + timedelta(days=1), base_paise=-1), format="json")
    assert r.status_code == 400 and "base_paise" in r.json()["error"]["fields"]
    r = c.post(PRICE_LISTS, {"active_from": today.isoformat()}, format="json")
    assert r.status_code == 400 and "per_branch_paise" in r.json()["error"]["fields"]


def test_move_to_current_prices(w):
    c = rackline()
    c.post(PRICE_LISTS, price_body(timezone.localdate(), base_paise=1_499_00, per_branch_paise=3_500_00), format="json")
    plan = c.get(console_plan(w.gym)).json()
    assert plan["current_prices"]["active_from"] == timezone.localdate().isoformat()
    assert plan["base_paise"] == PRICES["base_paise"]  # a new list never reprices a gym by itself

    r = c.post(f"{console_plan(w.gym)}current-prices/")
    assert r.status_code == 200
    moved = r.json()
    assert moved["base_paise"] == 1_499_00 and moved["monthly_paise"] == 1_499_00 + 2 * 3_500_00 and moved["current_prices"] is None
    row = AuditLog.objects.get(action="billing.prices_moved")
    assert row.gym == w.gym and row.before["base_paise"] == PRICES["base_paise"] and row.after["base_paise"] == 1_499_00
    assert c.post(f"{console_plan(w.gym)}current-prices/").json()["error"]["code"] == "already_current"


# Opening gyms

def test_a_new_gym_gets_a_plan_for_one_branch_on_todays_prices(prices):
    made = create_gym(name="Pulse", slug="pulse", timezone_name="Asia/Kolkata", branch="Kochi", owner_email="anil@pulse.in",
                      owner_name="Anil", owner_password="first-pass-123")
    plan = GymBilling.objects.get(gym=made.gym)
    assert plan.price_list == prices and plan.branch_quota == 1 and plan.prices() == prices.prices()
    assert plan.billing_day == min(clock.today(made.gym).day, 28) and plan.whatsapp_mode == "shared"


def test_no_gym_opens_before_rackline_has_prices(db):
    with pytest.raises(RuleBroken) as e:
        create_gym(name="Pulse", slug="pulse", timezone_name="Asia/Kolkata", branch="Kochi", owner_email="anil@pulse.in",
                   owner_name="Anil", owner_password="first-pass-123")
    assert e.value.rule_code == "no_prices" and not Gym.objects.filter(slug="pulse").exists()


def test_a_gym_with_no_plan_is_told_so_not_crashed(w):
    GymBilling.objects.filter(gym=w.gym).delete()
    r = new_branch(w.client(w.admin), "C")
    assert r.status_code == 409 and r.json()["error"]["code"] == "no_plan"


def test_existing_gyms_get_a_plan_for_their_open_branches(db):
    migration = importlib.import_module("apps.billing.migrations.0002_plans_for_existing_gyms")
    gym = Gym.objects.create(name="Old Iron", slug="old-iron")
    for name in ("A", "B", "C"):
        Branch.objects.create(gym=gym, name=name, is_active=name != "C")
    empty = Gym.objects.create(name="Empty", slug="empty")
    migration.plans_for_gyms(django_apps, None)
    plan = GymBilling.objects.get(gym=gym)
    assert plan.branch_quota == 2 and plan.whatsapp_mode == "shared" and plan.base_paise == 0
    assert GymBilling.objects.get(gym=empty).branch_quota == 1  # a plan never has room for none
    assert PriceList.objects.count() == 1


# Asking for more branches

def test_admin_asks_rackline_approves_and_the_quota_goes_up_at_once(w):
    admin = w.client(w.admin)
    assert new_branch(admin, "C").json()["error"]["code"] == "branch_limit"
    asked = ask(w, note="Opening in Kakkanad")
    assert asked["status"] == "asked" and asked["asked_by_name"] == w.admin.user.name and asked["pro_rata_paise"] is None
    assert admin.get(PLAN).json()["last_request"]["id"] == asked["id"]
    again = admin.post(ASKS, {"count": 1}, format="json")
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_asked"

    c = rackline()
    row = c.get(CONSOLE_ASKS, {"status": "asked"}).json()["results"][0]
    assert (row["gym_name"], row["branch_quota"], row["branches_in_use"], row["note"]) == (w.gym.name, 2, 2, "Opening in Kakkanad")
    r = c.post(f"{CONSOLE_ASKS}{asked['id']}/approve/")
    assert r.status_code == 200, r.content
    done = r.json()
    cost = services.pro_rata(PRICES["per_branch_paise"], 1, 1, clock.today(w.gym))
    assert done["status"] == "approved" and done["branch_quota"] == 3 and done["decided_by_name"] == "Rackline Ops"
    assert (done["pro_rata_paise"], done["charged_from"], done["charged_to"]) == (cost.amount_paise, cost.charged_from.isoformat(), cost.charged_to.isoformat())
    assert done["days_charged"] == cost.days and done["rate_paise"] == PRICES["per_branch_paise"]
    assert new_branch(admin, "C").status_code == 201
    plan = admin.get(PLAN).json()
    assert plan["branch_quota"] == 3 and plan["branches_in_use"] == 3 and plan["last_request"]["status"] == "approved"
    assert c.post(f"{CONSOLE_ASKS}{asked['id']}/approve/").json()["error"]["code"] == "decided"
    assert c.post(f"{CONSOLE_ASKS}{asked['id']}/decline/", {"reason": "x"}, format="json").json()["error"]["code"] == "decided"

    log = {a.action: a for a in AuditLog.objects.filter(gym=w.gym, action__startswith="branch_request.")}
    assert set(log) == {"branch_request.asked", "branch_request.approved"}
    assert log["branch_request.approved"].before == {"branch_quota": 2}
    assert log["branch_request.approved"].after == {"branch_quota": 3, "pro_rata_paise": cost.amount_paise}


def test_rackline_declines_with_a_reason(w):
    asked = ask(w, count=2)
    c = rackline()
    r = c.post(f"{CONSOLE_ASKS}{asked['id']}/decline/", {"reason": "  "}, format="json")
    assert r.status_code == 400 and r.json()["error"]["fields"]["reason"] == ["Say why, so the gym's admin knows"]
    r = c.post(f"{CONSOLE_ASKS}{asked['id']}/decline/", {"reason": "Settle the October invoice first"}, format="json")
    assert r.json()["status"] == "declined" and r.json()["pro_rata_paise"] is None
    last = w.client(w.admin).get(PLAN).json()
    assert last["branch_quota"] == 2 and last["last_request"]["decline_reason"] == "Settle the October invoice first"
    assert AuditLog.objects.get(action="branch_request.declined").after == {"reason": "Settle the October invoice first"}
    assert ask(w)["status"] == "asked"  # once answered, they can ask again


def test_gym_admins_cant_approve_their_own(w):
    asked = ask(w)
    for c in (w.client(w.admin), w.client(w.desk)):
        assert c.post(f"{CONSOLE_ASKS}{asked['id']}/approve/").status_code == 403
        assert c.post(f"{CONSOLE_ASKS}{asked['id']}/decline/", {"reason": "x"}, format="json").status_code == 403
    # A Rackline admin who also works at the gym leaves its requests to someone else.
    ops = User.objects.create_superuser(email="ops@rackline.in", password="pass12345", name="Ops")
    GymRole.objects.create(user=ops, gym=w.gym, role=GymRole.ADMIN)
    c = APIClient()
    c.force_authenticate(ops)
    assert c.post(f"{CONSOLE_ASKS}{asked['id']}/approve/").json()["error"]["code"] == "own_gym"
    assert BranchRequest.objects.get(pk=asked["id"]).status == "asked"
    assert GymBilling.objects.get(gym=w.gym).branch_quota == 2


def test_another_gyms_request_is_not_found(w, other):
    theirs = ask(other)
    c = w.client(w.admin)
    assert c.get(f"{ASKS}{theirs['id']}/").status_code == 404
    assert [r["id"] for r in c.get(ASKS).json()["results"]] == []
    assert c.get(PLAN).json()["last_request"] is None


def test_only_admins_see_the_plan_and_ask(w):
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(PLAN).status_code == 403
        assert c.get(ASKS).status_code == 403
        assert c.post(ASKS, {"count": 1}, format="json").status_code == 403


@pytest.mark.parametrize("count", [0, 6])
def test_a_request_asks_for_one_to_five(w, count):
    r = w.client(w.admin).post(ASKS, {"count": count}, format="json")
    assert r.status_code == 400 and "count" in r.json()["error"]["fields"]


def test_a_suspended_gyms_admins_still_see_their_plan(w):
    w.gym.status = Gym.SUSPENDED
    w.gym.save()
    assert w.client(w.admin).get(PLAN).status_code == 200
    assert w.client(w.admin).post(ASKS, {"count": 1}, format="json").json()["error"]["code"] == "gym_suspended"
    assert w.client(w.desk).get(PLAN).json()["error"]["code"] == "gym_suspended"


def test_console_requests_list_keeps_a_query_budget(w, other, django_assert_max_num_queries):
    ask(w)
    ask(other)
    for i in range(3):
        g = World(f"g{i}", n=2 + i)
        ask(g)
    c = rackline()
    with django_assert_max_num_queries(3):
        rows = c.get(CONSOLE_ASKS).json()
    assert rows["count"] == 5 and all(r["branches_in_use"] == 2 for r in rows["results"])
    assert c.get(CONSOLE_ASKS, {"gym": w.gym.id}).json()["count"] == 1


# What approving costs: the per-branch fee × days left ÷ days in the billing month, to the rupee

@pytest.mark.parametrize("billing_day, on, period, starts, ends, amount", [
    (1, date(2026, 2, 15), 28, date(2026, 2, 1), date(2026, 2, 28), 1_550_00),    # 14 of 28 days
    (1, date(2026, 4, 21), 30, date(2026, 4, 1), date(2026, 4, 30), 1_033_00),    # 10 of 30: ₹1,033.33
    (1, date(2026, 1, 31), 31, date(2026, 1, 1), date(2026, 1, 31), 100_00),      # the last day: 1 of 31
    (1, date(2026, 3, 1), 31, date(2026, 3, 1), date(2026, 3, 31), 3_100_00),     # the billing day: all of it
    (15, date(2026, 3, 10), 28, date(2026, 2, 15), date(2026, 3, 14), 554_00),    # 5 of 28: ₹553.57 rounds up
    (15, date(2026, 3, 15), 31, date(2026, 3, 15), date(2026, 4, 14), 3_100_00),
    (28, date(2026, 12, 31), 31, date(2026, 12, 28), date(2027, 1, 27), 2_800_00),  # across the new year: 28 of 31
    (28, date(2027, 2, 27), 31, date(2027, 1, 28), date(2027, 2, 27), 100_00),
])
def test_pro_rata_across_month_ends(billing_day, on, period, starts, ends, amount):
    cost = services.pro_rata(3_100_00, 1, billing_day, on)
    assert (cost.period_days, cost.charged_from, cost.charged_to, cost.amount_paise) == (period, on, ends, amount)
    assert services.billing_month(billing_day, on) == (starts, ends)


def test_pro_rata_rounds_half_a_rupee_up_and_counts_every_branch():
    assert services.pro_rata(1_00, 1, 1, date(2026, 2, 15)).amount_paise == 100  # 50 paise is a rupee
    assert services.pro_rata(3_100_00, 2, 1, date(2026, 2, 15)).amount_paise == 3_100_00
    assert services.pro_rata(0, 3, 1, date(2026, 2, 15)).amount_paise == 0
