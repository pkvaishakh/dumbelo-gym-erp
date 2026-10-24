"""A trainer's Home: their own check-in, their members by status and who came in today, and their personal training."""
from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.attendance.services import check_in
from apps.members.models import Member, Plan
from apps.members.services import mark_session, sell

TODAY = "/api/members/today/"


def ok(r):
    assert r.status_code == 200, r.content
    return r.json()


def pt_plan(w, sessions=3):
    return Plan.objects.create(gym=w.gym, name=f"PT {sessions}", kind=Plan.PT, months=3, sessions=sessions, price_paise=600000)


def test_a_trainers_day(w):
    d = ok(w.client(w.trainer).get(TODAY))
    assert d["checked_in"] is None and d["in_today"] == [] and d["pt"] == []
    assert d["statuses"]["active"] == 1 and sum(d["statuses"].values()) == 1  # only their own member, Asha

    check_in(w.a, staff=w.trainer, source="qr")
    check_in(w.a, member=w.member, source="desk")
    stranger = w.new_member("Ravi", "9800000099", w.a)  # not theirs: never counted or shown
    sell(stranger, w.monthly, by=w.desk, starts=w.today)
    check_in(w.a, member=stranger, source="desk")
    sub = sell(w.member, pt_plan(w, sessions=3), by=w.desk, starts=w.today - timedelta(days=1))
    mark_session(sub, by=w.trainer)

    d = ok(w.client(w.trainer).get(TODAY))
    assert d["checked_in"]["branch_name"] == "A" and d["checked_in"]["time"].endswith("M")
    assert [(m["name"], m["branch_name"]) for m in d["in_today"]] == [("Asha", "A")]
    [pt] = d["pt"]
    assert (pt["name"], pt["marked_today"], pt["pt"]["sessions"], pt["pt"]["sessions_used"]) == ("Asha", True, 3, 1)
    assert "price_paise" not in pt["pt"] and "balance_paise" not in str(d)
    assert sum(d["statuses"].values()) == 1


def test_only_trainers_have_a_trainers_day(w):
    for c in (w.client(w.admin), w.client(w.desk), w.member_client()):
        assert c.get(TODAY).status_code == 403


def test_a_trainers_day_costs_the_same_for_more_members(w):
    pt = pt_plan(w, sessions=10)

    def grow(n):
        for _ in range(n):
            i = Member.objects.count()
            m = w.new_member(f"Member {i}", f"97{6000 + i:08d}", w.a, trainer=w.trainer)
            sell(m, w.monthly, by=w.desk, starts=w.today - timedelta(days=3))
            mark_session(sell(m, pt, by=w.desk, starts=w.today - timedelta(days=3)), by=w.trainer)
            check_in(w.a, member=m, source="desk")

    def cost():
        with CaptureQueriesContext(connection) as q:
            ok(w.client(w.trainer).get(TODAY))
        return len(q.captured_queries)

    grow(2)
    few = cost()
    grow(5)
    assert cost() == few
