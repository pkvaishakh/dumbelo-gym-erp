"""Admins correct a plan already sold: its plan, offer, price or dates, with a reason, audited. Money already paid stays."""
from datetime import timedelta

from apps.audit.models import AuditLog
from apps.core import clock
from apps.members.models import Member, Offer, Plan
from apps.members.services import sell


def correct(w, sub, role=None, **body):
    return w.client(role or w.admin).post(f"/api/subscriptions/{sub.id}/correct/", {"reason": "Sold wrong", **body}, format="json")


def balance(w):
    return Member.objects.get(pk=w.member.pk).balance_paise()


def test_only_admins_correct_and_a_reason_is_needed(w):
    sub = w.member.current_subscription()
    assert correct(w, sub, role=w.desk, ends=str(sub.ends + timedelta(days=2))).status_code == 403
    r = w.client(w.admin).post(f"/api/subscriptions/{sub.id}/correct/", {"ends": str(sub.ends + timedelta(days=2))}, format="json")
    assert r.status_code == 400 and "reason" in r.json()["error"]["fields"]


def test_a_new_start_moves_the_end_with_the_plan_and_is_audited(w):
    sub = w.member.current_subscription()
    starts = w.today - timedelta(days=10)
    r = correct(w, sub, starts=str(starts))
    assert r.status_code == 200, r.content
    assert r.json()["starts"] == str(starts) and r.json()["ends"] == str(clock.plan_end(starts, 1))
    log = AuditLog.objects.get(action="subscription.corrected")
    assert log.before["starts"] == str(sub.starts) and log.after["reason"] == "Sold wrong"


def test_an_end_date_given_by_hand_wins(w):
    sub = w.member.current_subscription()
    r = correct(w, sub, ends=str(sub.ends + timedelta(days=5)))
    assert r.status_code == 200 and r.json()["ends"] == str(sub.ends + timedelta(days=5)) and r.json()["starts"] == str(sub.starts)
    assert correct(w, sub, ends=str(sub.starts - timedelta(days=1))).json()["error"]["code"] == "dates_invalid"


def test_switching_plan_takes_its_price_and_length_and_keeps_the_payment(w):
    quarterly = Plan.objects.create(gym=w.gym, name="Quarterly", months=3, price_paise=400000)
    sub = w.member.current_subscription()
    r = correct(w, sub, plan=quarterly.id)
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["plan_name"] == "Quarterly" and body["list_price_paise"] == body["price_paise"] == 400000
    assert body["ends"] == str(clock.plan_end(sub.starts, 3)) and body["paid_paise"] == 150000
    assert balance(w) == 250000


def test_a_plan_not_on_sale_or_not_at_the_branch_is_refused(w):
    sub = w.member.current_subscription()
    gone = Plan.objects.create(gym=w.gym, name="Old", months=1, price_paise=100000, on_sale=False)
    assert correct(w, sub, plan=gone.id).json()["error"]["code"] == "plan_not_on_sale"
    b_only = Plan.objects.create(gym=w.gym, name="B only", months=1, price_paise=200000)
    b_only.branches.set([w.b])
    assert correct(w, sub, plan=b_only.id).json()["error"]["code"] == "plan_not_at_branch"


def test_offers_work_the_price_out_again(w):
    sub = w.member.current_subscription()
    # Paid in full at ₹1,500, so an offer would leave it below what was paid.
    offer = Offer.objects.create(gym=w.gym, name="Diwali", percent_off=10, starts=w.today, ends=w.today + timedelta(days=5))
    assert correct(w, sub, offer=offer.id).json()["error"]["code"] == "price_below_paid"
    quarterly = Plan.objects.create(gym=w.gym, name="Quarterly", months=3, price_paise=400000)
    r = correct(w, sub, plan=quarterly.id, offer=offer.id)
    assert r.status_code == 200 and r.json()["price_paise"] == 360000 and r.json()["offer_name"] == "Diwali"
    r = correct(w, sub, offer=None)
    assert r.status_code == 200 and r.json()["price_paise"] == 400000 and r.json()["offer"] is None


def test_a_price_by_hand_never_below_what_was_paid(w):
    sub = w.member.current_subscription()
    r = correct(w, sub, price_paise=100000)
    assert r.status_code == 409 and r.json()["error"]["code"] == "price_below_paid"
    assert "₹1,500 has been paid" in r.json()["error"]["message"]
    r = correct(w, sub, price_paise=180000)
    assert r.status_code == 200 and balance(w) == 30000


def test_a_frozen_plans_dates_and_overlaps_are_refused(w):
    sub = w.member.current_subscription()
    nxt = sell(w.member, w.monthly, by=w.desk)  # the renewal, from the day after this one ends
    r = correct(w, sub, ends=str(nxt.starts + timedelta(days=3)))
    assert r.status_code == 409 and r.json()["error"]["code"] == "plans_overlap"
    w.client(w.desk).post(f"/api/subscriptions/{sub.id}/freeze/", {"until": str(w.today + timedelta(days=2))}, format="json")
    assert correct(w, sub, ends=str(sub.ends - timedelta(days=1))).json()["error"]["code"] == "frozen"
    assert correct(w, sub, price_paise=sub.price_paise).json()["error"]["code"] == "nothing_changed"


def test_another_gyms_plan_is_not_a_choice(w):
    from tests.conftest import World

    other = World(slug="other", n=1)
    r = correct(w, w.member.current_subscription(), plan=other.monthly.id)
    assert r.status_code == 400 and "plan" in r.json()["error"]["fields"]
