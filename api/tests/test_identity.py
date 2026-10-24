"""One login per person across every gym, found by username: never duplicated, never taken over by another gym or
by someone at the desk, and only ever opening the gyms the person has a role in."""
import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.accounts import usernames
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.gyms.models import GymRole
from apps.members.models import Member


def login(username, password):
    return APIClient().post("/api/auth/login/", {"username": username, "password": password}, format="json")


def set_login(w, member, **body):
    r = w.client(w.desk).post(f"/api/members/{member.id}/set-login/", body, format="json")
    member.refresh_from_db()
    return r


# ---- usernames ----

@pytest.mark.parametrize("email,name,base", [
    ("Ravi.K+gym@x.in", "Ravi Kumar", "ravi.k"),
    ("ab@x.in", "Aarav Reddy", "aarav.reddy"),  # too short: the name instead
    (None, "Zoë  O'Brien", "zoe.o.brien"),
    ("98000@x.in", "", "user.98000"),  # never only digits: it would look like a phone
    (None, "मीरा", "member"),  # nothing usable: a plain start, numbers come after
])
def test_a_username_starts_from_the_email_or_name(email, name, base):
    assert usernames.base_from(email, name) == base


@pytest.mark.parametrize("value,problem", [
    ("ab", "Use at least 3 characters"),
    ("a" * 31, "Use 30 characters or fewer"),
    ("meera iyer", "Use only letters, numbers, full stops and underscores"),
    (".meera", "A username can't start or end with a full stop, or have two in a row"),
    ("meera..iyer", "A username can't start or end with a full stop, or have two in a row"),
    ("9800000001", "Add a letter: a username can't be only numbers"),
    ("admin", "That username isn't available"),
    ("meera_iyer.2", None),
])
def test_username_rules(value, problem):
    assert usernames.problem(value) == problem


def test_suggestions_skip_taken_names(w):
    User.objects.create_user(username="nisha", password="x", name="Nisha")
    User.objects.create_user(username="nisha_", password="x", name="Nisha")
    assert usernames.suggest(email="nisha@x.in")[:2] == ["nisha2", "nisha3"]
    assert usernames.generate(name="Nisha") == "nisha2"


def test_capitals_dont_make_a_second_username(w):
    with pytest.raises(Exception):
        User.objects.create_user(username="ADMIN0", password="x", name="Copy")
    assert login("ADMIN0", "pass12345").status_code == 200


def test_people_can_share_a_phone_but_not_a_username(w):
    a = User.objects.create_user(username="ravi", password="x", name="Ravi", phone="9811100000")
    b = User.objects.create_user(username="priya", password="x", name="Priya", phone="98111 00000")  # his wife
    assert a.phone == b.phone == "+919811100000"


# ---- the check the forms call as people type ----

def test_username_check(w):
    c = w.client(w.desk)
    ok = c.get("/api/usernames/check/", {"username": "@Fresh.Name"}).json()
    assert ok == {"username": "fresh.name", "available": True, "problem": None, "name": None, "suggestions": []}
    taken = c.get("/api/usernames/check/", {"username": "trainer0", "name": "Arun"}).json()
    assert not taken["available"] and taken["problem"] == "That username is taken" and taken["name"] == "Trainer0"
    assert taken["suggestions"] == ["trainer02", "trainer03", "trainer04"]
    User.objects.create_user(username="ravi.k", password="x", name="Ravi")
    assert c.get("/api/usernames/check/", {"username": "ravi.k"}).json()["suggestions"][:2] == ["ravi_k", "ravi.k2"]
    reserved = c.get("/api/usernames/check/", {"username": "admin", "email": "anil@pulse.in"}).json()
    assert reserved["problem"] == "That username isn't available" and reserved["suggestions"][0] == "admin2"
    assert c.get("/api/usernames/check/", {"email": "anil@pulse.in"}).json()["suggestions"][0] == "anil"


def test_username_check_is_for_staff_only_and_hides_dumbelos_team(w):
    assert w.member_client().get("/api/usernames/check/", {"username": "admin0"}).status_code == 403
    User.objects.create_user(username="ops.team", password="x", name="Dumbelo Ops", is_staff=True)
    r = w.client(w.desk).get("/api/usernames/check/", {"username": "ops.team"}).json()
    assert not r["available"] and r["name"] is None


# ---- the desk can never take over someone else's login ----

def test_a_member_with_the_admins_phone_gets_their_own_login(w):
    """The old way found a login by phone and reset its password: a receptionist could take over the admin."""
    w.admin.user.phone = w.member.phone
    w.admin.user.save()
    r = set_login(w, w.member, password="desk-chose")
    assert r.status_code == 200 and r.json()["linked"] is False
    w.member.refresh_from_db()
    assert w.member.user != w.admin.user
    w.admin.user.refresh_from_db()
    assert w.admin.user.check_password("pass12345")


def test_the_desk_cant_reset_a_staff_login_through_a_member_profile(w):
    set_login(w, w.member, existing_username=w.trainer.user.username)  # the trainer also trains here
    w.member.refresh_from_db()
    assert w.member.user == w.trainer.user
    assert GymRole.objects.get(user=w.trainer.user, gym=w.gym).role == GymRole.TRAINER  # one role per gym
    r = set_login(w, w.member, password="desk-chose")
    assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"
    w.trainer.user.refresh_from_db()
    assert w.trainer.user.check_password("pass12345")


def test_a_login_shared_with_another_gym_is_only_its_owners_to_change(w, other):
    set_login(other, other.member, password="theirs-123")
    username = other.member.user.username
    r = set_login(w, w.member, existing_username=username)
    assert r.status_code == 200 and r.json() == {"username": username, "name": other.member.name, "linked": True}
    for body in ({"password": "taken-over"}, {"username": "taken.over"}):
        r = set_login(w, w.member, **body)
        assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"
    user = User.objects.get(username=username)
    assert user.check_password("theirs-123")


def test_a_role_switched_off_elsewhere_still_counts(w, other):
    """Switched-off roles can come back on, and the login with them: so it isn't this gym's to change either."""
    GymRole.objects.create(user=w.trainer.user, gym=other.gym, role=GymRole.TRAINER, is_active=False)
    r = w.client(w.admin).post(f"/api/staff/{w.trainer.id}/set-password/", {"password": "Front-desk-77"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"


def test_this_gyms_own_member_login_can_be_reset_and_renamed(w):
    set_login(w, w.member, password="first-123")
    r = set_login(w, w.member, password="second-123", username="Asha.Fit")
    assert r.status_code == 200 and r.json()["username"] == "asha.fit"
    assert login("asha.fit", "second-123").status_code == 200
    assert AuditLog.objects.filter(action="member.login_set").count() == 2


# ---- one person, one login, many gyms ----

def test_a_member_at_two_gyms_is_one_login(w, other):
    set_login(w, w.member, password="mine-1234")
    asha = w.member.user
    r = set_login(other, other.member, existing_username="ASHA")
    assert r.status_code == 200 and r.json()["linked"] is True
    assert User.objects.filter(name="Asha").count() == 1

    tokens = login("asha", "mine-1234").json()
    me = APIClient()
    me.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert sorted(r["gym"] for r in me.get("/api/me/").json()["roles"]) == ["iron", "steel"]
    for gym, profile in ((w.gym, w.member), (other.gym, other.member)):
        me.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_GYM=gym.slug)
        assert [m["id"] for m in me.get("/api/members/").json()["results"]] == [profile.id]  # each gym's own profile
    assert asha.gym_roles.count() == 2


def test_linking_needs_a_real_login_that_isnt_dumbelos_or_already_here(w):
    User.objects.create_user(username="ops.team", password="x", name="Ops", is_staff=True)
    set_login(w, w.member, password="mine-1234")
    second = w.new_member("Ravi", "9800000002", w.a)
    for name, message in (("nobody", "No one signs in with that username"),
                          ("ops.team", "That's a Dumbelo team login. Use the person's own username."),
                          ("asha", "@asha is already Asha's login here")):
        r = set_login(w, second, existing_username=name)
        assert r.status_code == 400 and r.json()["error"]["fields"]["existing_username"] == [message]


def test_one_member_profile_per_login_in_a_gym(w):
    set_login(w, w.member, password="mine-1234")
    with pytest.raises(IntegrityError):
        Member.objects.create(gym=w.gym, code="M-X", name="Copy", phone="+919800000009", home_branch=w.a, user=w.member.user)


def test_new_member_with_a_login(w, other):
    desk = w.client(w.desk)
    base = {"name": "Kiran Rao", "phone": "9800000011", "home_branch": w.a.id}
    r = desk.post("/api/members/", {**base, "username": "trainer0", "password": "secret1"}, format="json")
    assert r.status_code == 400 and r.json()["error"]["fields"]["username"] == ["That username is taken"]
    assert not Member.objects.filter(phone="+919800000011").exists()  # all or nothing
    r = desk.post("/api/members/", {**base, "password": "secret1"}, format="json")
    assert r.status_code == 201 and r.json()["username"] == "kiran.rao" and r.json()["has_login"] is True
    set_login(other, other.member, password="theirs-123")
    r = desk.post("/api/members/", {**base, "phone": "9800000012", "existing_username": other.member.user.username}, format="json")
    assert r.status_code == 201 and r.json()["username"] == other.member.user.username


def test_archiving_by_edit_closes_the_gym_to_the_member(w):
    set_login(w, w.member, password="mine-1234")
    desk = w.client(w.desk)
    assert desk.patch(f"/api/members/{w.member.id}/", {"is_archived": True}, format="json").status_code == 200
    role = GymRole.objects.get(user=w.member.user, gym=w.gym)
    assert role.is_active is False and AuditLog.objects.filter(action="member.archived").exists()
    assert desk.patch(f"/api/members/{w.member.id}/?archived=true", {"is_archived": False}, format="json").status_code == 200
    role.refresh_from_db()
    assert role.is_active and AuditLog.objects.filter(action="member.restored").exists()


def test_a_shared_logins_phone_stays_its_owners(w, other):
    set_login(other, other.member, password="theirs-123")
    set_login(w, w.member, existing_username=other.member.user.username)
    w.client(w.desk).patch(f"/api/members/{w.member.id}/", {"phone": "9800000055"}, format="json")
    user = User.objects.get(pk=other.member.user_id)
    assert user.phone == other.member.phone  # this gym's record changed, not their login


# ---- staff ----

def test_add_staff_makes_a_login_with_a_username(w):
    admin = w.client(w.admin)
    r = admin.post("/api/staff/", {"name": "Nisha", "email": "nisha.p@x.in", "role": "trainer", "branches": [w.a.id], "password": "first-pass-1"}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["username"] == "nisha.p"
    assert login("nisha.p", "first-pass-1").status_code == 200
    r = admin.post("/api/staff/", {"name": "Nisha Two", "username": "nisha.p", "role": "trainer", "branches": [w.a.id]}, format="json")
    assert r.json()["error"]["fields"]["username"] == ["That username is taken"]
    r = admin.post("/api/staff/", {"name": " ", "role": "trainer", "branches": [w.a.id]}, format="json")
    assert r.json()["error"]["fields"] == {"name": ["Enter their name"]}
    r = admin.post("/api/staff/", {"role": "trainer", "branches": [w.a.id]}, format="json")
    assert r.json()["error"]["fields"] == {"name": ["Enter their name"]}


def test_add_staff_who_already_signs_in_elsewhere(w, other):
    admin = w.client(w.admin)
    set_login(other, other.member, password="theirs-123")  # a member at steel comes to work at iron
    r = admin.post("/api/staff/", {"existing_username": other.member.user.username, "role": "receptionist", "branches": [w.a.id]}, format="json")
    assert r.status_code == 201 and r.json()["name"] == other.member.name
    user = User.objects.get(pk=other.member.user_id)
    assert user.check_password("theirs-123") and user.gym_roles.count() == 2
    assert User.objects.filter(name=other.member.name).count() == 1


@pytest.mark.parametrize("who,message", [
    ("desk", "Desk0 already works here as a receptionist"),
    ("member", "Asha is a member here, and a person has one role in a gym"),
    ("gone", "Gone used to work here. Turn them back on from their profile."),
])
def test_add_staff_wont_add_someone_twice(w, who, message):
    if who == "member":
        set_login(w, w.member, password="mine-1234")
        username = w.member.user.username
    elif who == "gone":
        username = w.role("gone@x.in", GymRole.TRAINER, [w.a]).user.username
        GymRole.objects.filter(user__username=username).update(is_active=False)
    else:
        username = w.desk.user.username
    r = w.client(w.admin).post("/api/staff/", {"existing_username": username, "role": "trainer", "branches": [w.a.id]}, format="json")
    assert r.status_code == 400 and r.json()["error"]["fields"]["existing_username"] == [message]


def test_staff_username_changes_follow_the_shared_login_rule(w, other):
    admin = w.client(w.admin)
    r = admin.patch(f"/api/staff/{w.desk.id}/", {"username": "Front.Desk"}, format="json")
    assert r.status_code == 200 and r.json()["username"] == "front.desk"
    r = admin.patch(f"/api/staff/{w.desk.id}/", {"username": "trainer0"}, format="json")
    assert r.json()["error"]["fields"]["username"] == ["That username is taken"]
    GymRole.objects.create(user=w.trainer.user, gym=other.gym, role=GymRole.TRAINER)
    r = admin.patch(f"/api/staff/{w.trainer.id}/", {"username": "mine.now"}, format="json")
    assert r.status_code == 409 and r.json()["error"]["code"] == "shared_login"


def test_a_gym_you_have_no_role_in_stays_invisible_to_a_linked_login(w, other):
    set_login(w, w.member, password="mine-1234")
    tokens = login("asha", "mine-1234").json()
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_GYM=other.gym.slug)
    assert c.get("/api/members/").status_code == 404


# ---- existing logins on the day usernames arrive ----

def test_existing_logins_get_usernames(db):
    import importlib

    from django.apps import apps

    give = importlib.import_module("apps.accounts.migrations.0003_give_usernames").give_usernames
    made = [
        User.objects.create_user(username=f"tmp{i}", password="x", **who) for i, who in enumerate([
            {"email": "Meera@Gym.in", "name": "Meera Iyer"},
            {"email": "meera@other.in", "name": "Meera Two"},  # same start: numbered
            {"phone": "9800000001", "name": "Aarav Reddy"},  # a member: from the name
            {"email": "dumbelo@dumbelo.demo", "name": "Dumbelo Admin", "is_staff": True},  # reserved
            {"email": "admin@gym.in", "name": "Gym Admin"},  # reserved, not Dumbelo's team
        ])
    ]
    give(apps, None)
    got = [User.objects.get(pk=u.pk).username for u in made]
    assert got == ["meera", "meera2", "aarav.reddy", "dumbelo.admin", f"admin.{made[4].pk}"]


def test_createsuperuser_takes_a_username(db, monkeypatch):
    """docs/deploy.md makes the first Dumbelo admin this way."""
    from django.core.management import call_command

    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "a-long-pass-from-a-manager")
    call_command("createsuperuser", "--noinput", username="Ops.Lead", name="Ops Lead")
    user = User.objects.get(username="ops.lead")
    assert user.is_superuser and login("ops.lead", "a-long-pass-from-a-manager").status_code == 200
