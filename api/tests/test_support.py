"""Rackline support access: who may open a window, what support sees inside it, and ending it early."""
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.gyms.models import SupportAccess


def support_client(gym_slug="iron"):
    """Someone from Rackline: a staff user with no role in the gym."""
    user = User.objects.create_user(email="help@rackline.in", password="pass12345", name="Ravi at Rackline", is_staff=True)
    c = APIClient()
    c.force_authenticate(user)
    c.credentials(HTTP_X_GYM=gym_slug)
    return c


def grant(client, hours=2):
    return client.post("/api/support-access/", {"hours": hours}, format="json")


def test_admin_grants_a_window_and_support_can_look_inside_it(w):
    support = support_client()
    assert support.get("/api/members/").status_code == 404  # no window: the gym may as well not exist

    r = grant(w.client(w.admin), 24)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["open"] is True and body["granted_by_name"] == w.admin.user.name
    assert "hours" not in body  # it is only an input: the window is its own two timestamps

    assert support.get("/api/members/").status_code == 200


def test_support_can_only_read(w):
    grant(w.client(w.admin))
    support = support_client()
    assert support.get("/api/members/").status_code == 200
    assert support.post("/api/branches/", {"name": "X"}, format="json").status_code == 403
    assert grant(support).status_code == 403  # and it can't extend its own window


def test_support_cannot_read_after_the_window_ends(w):
    c = w.client(w.admin)
    window = grant(c, 24).json()
    support = support_client()
    assert support.get("/api/members/").status_code == 200

    r = c.post(f"/api/support-access/{window['id']}/end/")
    assert r.status_code == 200 and r.json()["open"] is False
    assert support.get("/api/members/").status_code == 404


def test_a_window_that_ran_out_closes_itself(w):
    SupportAccess.objects.create(gym=w.gym, granted_by=w.admin.user, starts=timezone.now() - timedelta(hours=3), ends=timezone.now() - timedelta(hours=1))
    assert support_client().get("/api/members/").status_code == 404


def test_only_admins_grant_or_end(w):
    window = grant(w.client(w.admin)).json()
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get("/api/support-access/").status_code == 403
        assert grant(c).status_code == 403
        assert c.post(f"/api/support-access/{window['id']}/end/").status_code == 403


def test_another_gyms_window_is_not_found(w, other):
    theirs = grant(other.client(other.admin)).json()
    c = w.client(w.admin)
    assert c.post(f"/api/support-access/{theirs['id']}/end/").status_code == 404
    assert c.get("/api/support-access/").json()["count"] == 0  # and it isn't in your history


def test_access_cannot_be_granted_twice_over(w):
    c = w.client(w.admin)
    assert grant(c).status_code == 201
    r = grant(c, 24)
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_open"


def test_ending_an_access_that_is_over_says_so(w):
    c = w.client(w.admin)
    window = grant(c).json()
    assert c.post(f"/api/support-access/{window['id']}/end/").status_code == 200
    r = c.post(f"/api/support-access/{window['id']}/end/")
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_open"


def test_granting_and_ending_are_audited(w):
    c = w.client(w.admin)
    window = grant(c).json()
    c.post(f"/api/support-access/{window['id']}/end/")
    rows = AuditLog.objects.filter(gym=w.gym, object_type="SupportAccess", object_id=str(window["id"]))
    assert list(rows.order_by("at").values_list("action", flat=True)) == ["support.granted", "support.ended"]
    assert all(row.actor == w.admin.user for row in rows)
    ended = rows.get(action="support.ended")
    assert ended.before["ends"] != ended.after["ends"]  # the window was cut short, and by how much is on record


def test_history_is_newest_first_within_a_query_budget(w, django_assert_max_num_queries):
    c = w.client(w.admin)
    now = timezone.now()
    for days in range(6):
        SupportAccess.objects.create(gym=w.gym, granted_by=w.admin.user, starts=now - timedelta(days=days + 1), ends=now - timedelta(days=days, hours=22))
    with django_assert_max_num_queries(6):
        rows = c.get("/api/support-access/").json()["results"]
    assert [r["open"] for r in rows] == [False] * 6
    assert rows == sorted(rows, key=lambda r: r["starts"], reverse=True)
    assert rows[0]["granted_by_name"] == w.admin.user.name
