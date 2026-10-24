"""Rate limits, sign-out, page sizes and bad query values."""
import pytest

from apps.core import clock


def login(client, password="pass12345"):
    return client.post("/api/auth/login/", {"username": "admin0", "password": password}, content_type="application/json")


def test_login_is_rate_limited_per_account(w, client):
    codes = [login(client, "wrong").status_code for _ in range(11)]
    assert codes[:10] == [401] * 10 and codes[10] == 429
    assert login(client).json()["error"]["code"] == "throttled"  # the right password waits too
    other = client.post("/api/auth/login/", {"username": "desk0", "password": "pass12345"}, content_type="application/json")
    assert other.status_code == 200  # someone else on the same Wi-Fi can still sign in


def test_sign_out_kills_the_refresh_token(w, client):
    refresh = login(client).json()["refresh"]
    expired = {"HTTP_AUTHORIZATION": "Bearer not-a-valid-token"}  # sign-out still works with a dead access token
    assert client.post("/api/auth/logout/", {"refresh": refresh}, content_type="application/json", **expired).status_code == 200
    assert client.post("/api/auth/refresh/", {"refresh": refresh}, content_type="application/json").status_code == 401


def test_a_used_refresh_token_cant_be_used_again(w, client):
    refresh = login(client).json()["refresh"]
    assert client.post("/api/auth/refresh/", {"refresh": refresh}, content_type="application/json").status_code == 200
    assert client.post("/api/auth/refresh/", {"refresh": refresh}, content_type="application/json").status_code == 401


@pytest.mark.parametrize("gone", ["deleted", "inactive"])
def test_a_refresh_token_dies_with_its_account(w, client, gone):
    """After `seed_demo --reset` (accounts deleted) or a disabled login, a saved refresh token must not mint a new
    access token: the app would get 401 everywhere instead of being sent back to sign-in."""
    refresh = login(client).json()["refresh"]
    user = w.admin.user
    if gone == "deleted":
        w.admin.delete()
        user.delete()
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
    r = client.post("/api/auth/refresh/", {"refresh": refresh}, content_type="application/json")
    assert r.status_code == 401, r.content


def test_page_size_is_capped(w):
    for i in range(3):
        w.new_member(f"M{i}", f"96{6000 + i:08d}", w.a)
    r = w.client(w.admin).get("/api/members/?limit=100000").json()
    assert len(r["results"]) == 4  # every row fits; the cap is checked below
    from apps.core.params import Pages

    assert Pages.max_limit == 100


@pytest.mark.parametrize("url", [
    "/api/members/?branch=abc", "/api/members/?trainer=x", "/api/checkins/?member=abc", "/api/checkins/?staff=1.5",
    "/api/checkins/?branch=a", "/api/payments/collection/?branch=a", "/api/reports/summary/?branch=a",
    "/api/payments/?date=yesterday",
])
def test_bad_query_values_are_400_not_500(w, url):
    r = w.client(w.admin).get(url)
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid"


def test_time_label_is_the_same_on_every_os(w):
    from datetime import datetime, timezone

    assert clock.time_label(w.gym, datetime(2026, 1, 1, 0, 35, tzinfo=timezone.utc)) == "6:05 AM"  # IST is +5:30
    assert clock.time_label(w.gym, datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc)) == "12:30 PM"
    assert clock.time_label(w.gym, datetime(2026, 1, 1, 18, 45, tzinfo=timezone.utc)) == "12:15 AM"
