"""The landing page's demo form, and the leads it brings into the Console."""
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.leads.models import Lead
from apps.leads.services import take_lead

from .test_platform import dumbelo, support

ASK = "/api/leads/"
LEADS = "/api/platform/leads/"
FORM = {"name": "Anil Menon", "phone": "98470 12345", "gym_name": "Pulse Fitness", "city": "Kochi", "branches": "2-3",
        "utm_source": "google", "utm_campaign": "kerala-gyms"}


def ask(body=None, client=None, **headers):
    return (client or APIClient()).post(ASK, {**FORM, **(body or {})}, format="json", **headers)


def test_anyone_can_ask_for_a_demo(db):
    r = ask({"email": "anil@pulse.in", "note": "  We open a third   branch in May  "})
    assert r.status_code == 201, r.content
    assert r.json() == {"received": True}
    lead = Lead.objects.get()
    assert (lead.phone, lead.gym_name, lead.branches, lead.status) == ("+919847012345", "Pulse Fitness", "2-3", Lead.NEW)
    assert lead.note == "We open a third branch in May"
    assert (lead.utm_source, lead.utm_campaign) == ("google", "kerala-gyms")


def test_each_field_says_what_to_fix(db):
    r = ask({"name": " ", "phone": "12345", "gym_name": "", "city": "", "branches": "10", "email": "anil@"})
    assert r.status_code == 400
    fields = r.json()["error"]["fields"]
    assert fields["name"] == ["Enter your name"]
    assert fields["phone"] == ["Enter a 10-digit mobile number"]
    assert fields["gym_name"] == ["Enter your gym’s name"]
    assert fields["city"] == ["Enter your city"]
    assert fields["branches"] == ["Choose how many branches"]
    assert fields["email"] == ["Enter an email like you@gym.com, or leave it empty"]
    assert not Lead.objects.exists()


def test_asking_twice_keeps_one_lead(db):
    ask({"email": "anil@pulse.in"})
    ask({"phone": "+91 98470 12345", "branches": "4+"})  # the same number, written differently
    lead = Lead.objects.get()
    assert lead.branches == "4+" and lead.email == "anil@pulse.in"

    # A day later, or once someone has answered the first, it's a new ask.
    Lead.objects.update(created_at=timezone.now() - timedelta(days=2))
    ask()
    assert Lead.objects.count() == 2
    Lead.objects.filter(status=Lead.NEW).update(status=Lead.CONTACTED)
    take_lead({**FORM, "phone": "+919847012345"})
    assert Lead.objects.count() == 3


def test_a_bot_that_fills_the_hidden_field_is_thanked_and_dropped(db):
    r = ask({"website": "https://spam.example"})
    assert r.status_code == 201 and r.json() == {"received": True}
    assert not Lead.objects.exists()


def test_the_form_is_rate_limited_per_address(db):
    answers = [ask({"phone": f"98470000{n:02}"}) for n in range(11)]  # THROTTLE_LEAD: 10 an hour
    assert [r.status_code for r in answers[:10]] == [201] * 10 and answers[10].status_code == 429
    assert answers[10].json()["error"]["message"] == "We already have your request and will call you soon. To add something, try again in an hour."


def test_an_old_sign_in_in_the_browser_does_not_block_the_form(db):
    assert ask(HTTP_AUTHORIZATION="Bearer not-a-real-token").status_code == 201


def test_only_dumbelo_admins_see_leads(w):
    ask()
    lead = Lead.objects.get()
    for c in [w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client(), support()]:
        assert c.get(LEADS).status_code == 403
        assert c.get(f"{LEADS}{lead.id}/").status_code == 403
        assert c.post(f"{LEADS}{lead.id}/status/", {"status": "won"}, format="json").status_code == 403
    assert APIClient().get(LEADS).status_code == 401
    assert Lead.objects.get().status == Lead.NEW


def test_the_console_lists_filters_and_finds_leads_within_a_query_budget(db, django_assert_max_num_queries):
    for n in range(6):
        ask({"phone": f"98470000{n:02}", "gym_name": f"Gym {n}", "city": "Pune" if n % 2 else "Kochi"})
    c = dumbelo()
    first = Lead.objects.order_by("created_at").first()
    c.post(f"{LEADS}{first.id}/status/", {"status": "contacted"}, format="json")
    with django_assert_max_num_queries(4):
        r = c.get(LEADS)
    body = r.json()
    assert body["count"] == 6 and body["results"][0]["gym_name"] == "Gym 5"  # newest first
    assert body["results"][-1]["status_by_name"] == "Dumbelo Ops"
    assert body["results"][0]["branches_label"] == "2 to 3 branches"
    assert c.get(LEADS, {"status": "new"}).json()["count"] == 5
    assert c.get(LEADS, {"q": "pune"}).json()["count"] == 3
    assert c.get(LEADS, {"q": "p"}).json()["count"] == 6  # one letter is not a search
    assert c.get(LEADS, {"status": "maybe"}).status_code == 400


def test_moving_a_lead_along_is_audited(db):
    ask()
    lead = Lead.objects.get()
    c = dumbelo()
    r = c.post(f"{LEADS}{lead.id}/status/", {"status": "won"}, format="json")
    assert r.status_code == 200, r.content
    assert r.json()["status"] == "won" and r.json()["status_at"]
    log = AuditLog.objects.get(action="lead.status")
    assert (log.before, log.after, log.gym) == ({"status": "new"}, {"status": "won"}, None)
    assert c.post(f"{LEADS}{lead.id}/status/", {"status": "maybe"}, format="json").status_code == 400
    assert c.post(f"{LEADS}999999/status/", {"status": "won"}, format="json").status_code == 404


def test_console_home_counts_new_leads(db):
    for n in range(3):
        ask({"phone": f"98470000{n:02}"})
    Lead.objects.filter(pk=Lead.objects.first().pk).update(status=Lead.LOST)
    assert dumbelo().get("/api/platform/summary/").json()["leads"] == {"new": 2}
