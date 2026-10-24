"""Plans and offers are one list for the gym; the admin gives each to some branches, or to every branch."""
from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.audit.models import AuditLog
from apps.members.models import Offer, Plan


def names(r):
    assert r.status_code == 200, r.content
    return {row["name"] for row in r.json()["results"]}


def test_admin_gives_a_plan_to_branches(w):
    r = w.client(w.admin).post("/api/plans/", {"name": "Quarterly A", "months": 3, "price_paise": 400000, "branches": [w.a.id]}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["branches"] == [w.a.id]
    r = w.client(w.admin).patch(f"/api/plans/{r.json()['id']}/", {"branches": [w.a.id, w.b.id]}, format="json")
    assert sorted(r.json()["branches"]) == sorted([w.a.id, w.b.id])


SETTINGS = "/api/gym/settings/"


def test_a_gym_sets_how_long_its_month_runs_and_new_sales_follow_it(w):
    quarterly = Plan.objects.create(gym=w.gym, name="Quarterly", months=3, price_paise=400000)
    r = w.client(w.admin).patch(SETTINGS, {"month_days": 28}, format="json")
    assert r.status_code == 200 and r.json()["month_days"] == 28
    r = w.client(w.desk).post("/api/subscriptions/", {"member": w.member.id, "plan": quarterly.id}, format="json")
    assert r.status_code == 201, r.content
    sub = w.member.subscriptions.get(pk=r.json()["id"])
    assert sub.ends == sub.starts + timedelta(days=3 * 28 - 1)  # 84 days, the first one included
    assert w.client(w.admin).get("/api/me/").json()["roles"][0]["month_days"] == 28
    log = AuditLog.objects.get(action="gym.settings_changed")
    assert (log.before, log.after) == ({"month_days": 0}, {"month_days": 28})
    # Back to calendar months: 0.
    assert w.client(w.admin).patch(SETTINGS, {"month_days": 0}, format="json").json()["month_days"] == 0


def test_only_admins_set_the_month_and_within_reason(w):
    assert w.client(w.desk).patch(SETTINGS, {"month_days": 30}, format="json").status_code == 403
    r = w.client(w.admin).patch(SETTINGS, {"month_days": 61}, format="json")
    assert r.status_code == 400 and "month_days" in r.json()["error"]["fields"]
    r = w.client(w.admin).patch(SETTINGS, {"name": "Renamed", "month_days": 30}, format="json")
    assert r.json()["name"] == w.gym.name and r.json()["month_days"] == 30  # the name stays Dumbelo's to set


def test_a_membership_plan_needs_months(w):
    r = w.client(w.admin).post("/api/plans/", {"name": "Odd", "price_paise": 90000}, format="json")
    assert r.status_code == 400 and "months" in r.json()["error"]["fields"]


def test_no_branch_means_every_branch(w):
    assert w.monthly.branches.count() == 0
    assert "Monthly" in names(w.client(w.desk).get("/api/plans/"))
    assert "Monthly" in names(w.client(w.desk_b).get("/api/plans/"))


def test_desk_sees_only_its_branches_plans(w):
    Plan.objects.create(gym=w.gym, name="B only", months=1, price_paise=100000).branches.set([w.b])
    assert "B only" not in names(w.client(w.desk).get("/api/plans/"))
    assert "B only" in names(w.client(w.desk_b).get("/api/plans/"))
    assert "B only" not in names(w.client(w.trainer).get("/api/plans/"))
    assert "B only" not in names(w.member_client().get("/api/plans/"))


def test_admin_sees_every_plan_and_can_ask_for_one_branch(w):
    Plan.objects.create(gym=w.gym, name="B only", months=1, price_paise=100000).branches.set([w.b])
    assert {"Monthly", "B only"} <= names(w.client(w.admin).get("/api/plans/"))
    assert names(w.client(w.admin).get(f"/api/plans/?branch={w.a.id}")) == {"Monthly"}
    assert w.client(w.admin).get("/api/plans/?branch=abc").status_code == 400


def test_search_plans_and_offers_by_name(w):
    Plan.objects.create(gym=w.gym, name="Quarterly", months=3, price_paise=400000)
    Offer.objects.create(gym=w.gym, name="Diwali", percent_off=10, starts=w.today, ends=w.today)
    Offer.objects.create(gym=w.gym, name="Summer", percent_off=5, starts=w.today, ends=w.today)
    admin = w.client(w.admin)
    assert names(admin.get("/api/plans/?q=quart")) == {"Quarterly"}
    assert names(admin.get("/api/plans/?q=q")) == {"Monthly", "Quarterly"}  # too short: ignored
    assert names(admin.get("/api/offers/?q=%20diw%20")) == {"Diwali"}


def test_plan_not_given_to_the_members_branch_cant_be_sold(w):
    b_only = Plan.objects.create(gym=w.gym, name="B only", months=1, price_paise=100000)
    b_only.branches.set([w.b])
    r = w.client(w.admin).post("/api/subscriptions/", {"member": w.member.id, "plan": b_only.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "plan_not_at_branch"
    assert r.json()["error"]["message"] == "B only isn't sold at A"


def test_offer_given_to_another_branch_doesnt_apply(w):
    offer = Offer.objects.create(gym=w.gym, name="B Diwali", percent_off=10, starts=w.today, ends=w.today + timedelta(days=5))
    offer.branches.set([w.b])
    assert "B Diwali" not in names(w.client(w.desk).get("/api/offers/?current=true"))
    assert "B Diwali" in names(w.client(w.desk_b).get("/api/offers/?current=true"))
    r = w.client(w.admin).post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id, "offer": offer.id}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "offer_not_valid"
    offer.branches.add(w.a)
    r = w.client(w.admin).post("/api/subscriptions/", {"member": w.member.id, "plan": w.monthly.id, "offer": offer.id}, format="json")
    assert r.status_code == 201, r.content


def test_admin_gives_an_offer_to_branches(w):
    body = {"name": "A week", "amount_off_paise": 50000, "starts": str(w.today), "ends": str(w.today + timedelta(days=7)), "branches": [w.a.id]}
    r = w.client(w.admin).post("/api/offers/", body, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["branches"] == [w.a.id]
    r = w.client(w.admin).patch(f"/api/offers/{r.json()['id']}/", {"branches": []}, format="json")
    assert r.json()["branches"] == []


def test_desk_cant_give_plans_to_branches(w):
    r = w.client(w.desk).patch(f"/api/plans/{w.monthly.id}/", {"branches": [w.a.id]}, format="json")
    assert r.status_code == 403


def test_another_gyms_branch_is_refused(w, other):
    r = w.client(w.admin).patch(f"/api/plans/{w.monthly.id}/", {"branches": [other.a.id]}, format="json")
    assert r.status_code == 400 and "branches" in r.json()["error"]["fields"]


def test_plan_and_offer_lists_dont_grow_with_rows(w):
    def count(url):
        with CaptureQueriesContext(connection) as q:
            assert w.client(w.desk).get(url).status_code == 200
        return len(q)

    def grow(n):
        for i in range(n):
            p = Plan.objects.create(gym=w.gym, name=f"Plan {Plan.objects.count()}", months=1, price_paise=100000)
            p.branches.set([w.a, w.b])
            o = Offer.objects.create(gym=w.gym, name=f"Offer {i}", percent_off=5, starts=w.today, ends=w.today)
            o.branches.set([w.a])
            o.plans.set([p])

    grow(2)
    small = count("/api/plans/"), count("/api/offers/")
    grow(10)
    assert (count("/api/plans/"), count("/api/offers/")) == small
