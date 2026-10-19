"""WhatsApp accounts and templates: who may set them up, what a gym sees, and credentials that never come back out."""
import io
import json
import logging
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.billing.models import GymBilling
from apps.messages import accounts, crypto
from apps.messages.models import WhatsAppAccount, WhatsAppTemplate
from tests.test_platform import dumbelo, support

ACCOUNTS = "/api/platform/whatsapp-accounts/"
TEMPLATES = "/api/platform/whatsapp-templates/"
MINE = "/api/gym/whatsapp/"
TOKEN = "EAAGtest-access-token-0123456789-very-secret-tok9"
SECRET = "app-secret-abcdef0123456789-zz42"
SHARED = {"waba_id": "100000000000001", "phone_number_id": "200000000000001", "display_number": "+91 80000 00001",
          "access_token": TOKEN, "app_secret": SECRET}
PLAN_ENDING = {"kind": "plan_ending", "name": "plan_ending_v1", "language": "en", "body": "Hi {{1}}, your {{2}} at {{3}} ends on {{4}}.",
               "parameters": ["first_name", "plan", "gym", "end_date"], "status": "approved"}


@pytest.fixture(autouse=True)
def shared_number():
    """These tests add Dumbelo's shared number themselves, through the Console."""
    return None


def own(gym, n=2):
    return {"gym": gym.id, "waba_id": f"10000000000000{n}", "phone_number_id": f"20000000000000{n}",
            "display_number": f"+91 80000 0000{n}", "access_token": f"{TOKEN}-gym{n}", "app_secret": f"{SECRET}-gym{n}"}


def add(c, body=SHARED):
    r = c.post(ACCOUNTS, body, format="json")
    assert r.status_code == 201, r.content
    return r.json()


def secrets_in(*texts) -> list[str]:
    """Any credential (or a long piece of one) in the texts given."""
    found = []
    for text in texts:
        for secret in (TOKEN, SECRET, TOKEN[:20], SECRET[:16]):
            if secret in text:
                found.append(secret)
    return found


def audit_text() -> str:
    return json.dumps([[a.action, a.before, a.after] for a in AuditLog.objects.all()])


class Answer(io.BytesIO):
    """What urlopen hands back: a response to read, used in a `with`."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Meta:
    """Stands in for Meta's Graph API: remembers each request, answers with what the test says."""

    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.requests = answer, error, []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        if self.error:
            raise self.error
        return Answer(json.dumps(self.answer).encode())


def meta_error(status, body):
    return HTTPError("https://graph.facebook.com/x", status, "Error", hdrs=None, fp=io.BytesIO(json.dumps(body).encode()))


# ---- Who may ----

def test_only_dumbelo_admins_set_up_whatsapp(w):
    account = accounts.add_account(gym=None, **SHARED)
    for c in [w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client(), support()]:
        assert c.get(ACCOUNTS).status_code == 403
        assert c.get(f"{ACCOUNTS}{account.id}/").status_code == 403
        assert c.post(ACCOUNTS, own(w.gym), format="json").status_code == 403
        assert c.patch(f"{ACCOUNTS}{account.id}/", {"display_number": "+91 1"}, format="json").status_code == 403
        assert c.post(f"{ACCOUNTS}{account.id}/replace-credentials/", {"access_token": TOKEN + "x"}, format="json").status_code == 403
        assert c.post(f"{ACCOUNTS}{account.id}/test/").status_code == 403
        assert c.get(TEMPLATES).status_code == 403
        assert c.post(TEMPLATES, {**PLAN_ENDING, "account": account.id}, format="json").status_code == 403
        assert c.get(f"{TEMPLATES}kinds/").status_code == 403
    assert APIClient().get(ACCOUNTS).status_code == 401
    assert dumbelo().get(ACCOUNTS).status_code == 200


def test_accounts_are_never_deleted(w):
    c = dumbelo()
    account = add(c)
    assert c.delete(f"{ACCOUNTS}{account['id']}/").status_code == 405
    assert c.put(f"{ACCOUNTS}{account['id']}/", SHARED, format="json").status_code == 405


# ---- Adding and showing an account ----

def test_add_the_shared_number_and_a_gyms_own(w):
    c = dumbelo()
    shared = add(c)
    assert shared["is_shared"] is True and shared["gym"] is None and shared["status"] == "new"
    assert shared["access_token_last4"] == TOKEN[-4:] and shared["app_secret_last4"] == SECRET[-4:]
    assert shared["webhook_url"] == "http://testserver/api/whatsapp/webhook/" and shared["verify_token"]

    mine = add(c, own(w.gym))
    assert mine["gym"] == w.gym.id and mine["gym_name"] == w.gym.name and mine["is_shared"] is False
    assert mine["webhook_url"].endswith(f"/api/whatsapp/webhook/{WhatsAppAccount.objects.get(pk=mine['id']).webhook_slug}/")

    rows = c.get(ACCOUNTS).json()["results"]
    assert [r["id"] for r in rows] == [shared["id"], mine["id"]]  # the shared number first
    assert c.get(ACCOUNTS, {"gym": w.gym.id}).json()["count"] == 1

    added = AuditLog.objects.filter(action="whatsapp_account.added")
    assert added.count() == 2 and added.filter(gym=w.gym).count() == 1 and added.filter(gym=None).count() == 1
    assert added.first().after["credentials"] == ["access_token", "app_secret"]


def test_one_shared_number_one_account_a_gym_and_a_number_once(w, other):
    c = dumbelo()
    add(c)
    again = c.post(ACCOUNTS, {**SHARED, "phone_number_id": "299999999999999"}, format="json")
    assert again.status_code == 409 and again.json()["error"]["code"] == "account_exists"

    add(c, own(w.gym))
    second = c.post(ACCOUNTS, {**own(w.gym, 3)}, format="json")
    assert second.status_code == 409 and second.json()["error"]["code"] == "account_exists"

    same_number = c.post(ACCOUNTS, {**own(other.gym, 4), "phone_number_id": SHARED["phone_number_id"]}, format="json")
    assert same_number.status_code == 409 and same_number.json()["error"]["code"] == "number_taken"


def test_bad_input_is_a_field_error_that_never_repeats_a_credential(w):
    c = dumbelo()
    r = c.post(ACCOUNTS, {**SHARED, "phone_number_id": "../me/accounts", "access_token": TOKEN * 30, "app_secret": "short"}, format="json")
    assert r.status_code == 400
    fields = r.json()["error"]["fields"]
    assert {"phone_number_id", "access_token", "app_secret"} <= set(fields)
    assert not secrets_in(r.content.decode())
    assert c.post(ACCOUNTS, {**SHARED, "gym": 999999}, format="json").status_code == 400


# ---- Credentials: write-only, encrypted, and nowhere else ----

def test_no_response_log_line_or_audit_row_holds_a_credential(w, caplog):
    caplog.set_level(logging.DEBUG)
    c = dumbelo()
    responses = [c.post(ACCOUNTS, SHARED, format="json")]
    pk = responses[0].json()["id"]
    responses += [c.post(ACCOUNTS, own(w.gym), format="json")]
    responses += [c.get(ACCOUNTS), c.get(f"{ACCOUNTS}{pk}/")]
    responses += [c.patch(f"{ACCOUNTS}{pk}/", {"display_number": "+91 80000 00009"}, format="json")]
    responses += [c.post(f"{ACCOUNTS}{pk}/replace-credentials/", {"access_token": TOKEN + "-new", "app_secret": SECRET + "-new"}, format="json")]
    # Meta's error quoting the token back must not carry it into the record either
    with mock.patch("apps.messages.meta.urlopen", Meta(error=meta_error(401, {"error": {"message": f"Bad token {TOKEN}-new", "code": 190}}))):
        responses += [c.post(f"{ACCOUNTS}{pk}/test/")]
    GymBilling.objects.filter(gym=w.gym).update(whatsapp_mode=GymBilling.OWN)
    responses += [w.client(w.admin).get(MINE)]

    assert all(r.status_code in (200, 201) for r in responses), [r.content for r in responses]
    assert not secrets_in(*(r.content.decode() for r in responses))
    assert not secrets_in(caplog.text), "a credential reached the log"
    assert not secrets_in(audit_text()), "a credential reached the audit log"
    replaced = AuditLog.objects.get(action="whatsapp_account.credentials_replaced")
    assert replaced.after == {"credentials": ["access_token", "app_secret"]} and replaced.before is None
    assert "Bad token …" in WhatsAppAccount.objects.get(pk=pk).last_error


def test_credentials_are_encrypted_in_the_database_and_read_back(w):
    account = accounts.add_account(gym=None, **SHARED)
    with connection.cursor() as cur:
        cur.execute("SELECT access_token, app_secret FROM gym_messages_whatsappaccount WHERE id = %s", [account.pk])
        raw_token, raw_secret = cur.fetchone()
    assert TOKEN not in raw_token and SECRET not in raw_secret
    assert crypto.decrypt(raw_token) == TOKEN and crypto.decrypt(raw_secret) == SECRET

    fresh = WhatsAppAccount.objects.get(pk=account.pk)
    assert fresh.access_token == TOKEN and fresh.app_secret == SECRET
    assert crypto.encrypt(TOKEN) != crypto.encrypt(TOKEN)  # a fresh IV each time, so equal tokens don't look equal


def test_encryption_survives_a_key_rotation(w, settings):
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    settings.FIELD_ENCRYPTION_KEY = [old]
    account = accounts.add_account(gym=None, **SHARED)

    settings.FIELD_ENCRYPTION_KEY = [new, old]  # step 1: the new key first, the old one still there to read
    assert WhatsAppAccount.objects.get(pk=account.pk).access_token == TOKEN
    call_command("rotate_credentials", stdout=io.StringIO())  # step 2: everything written again with the new key

    settings.FIELD_ENCRYPTION_KEY = [new]  # step 3: the old key goes
    fresh = WhatsAppAccount.objects.get(pk=account.pk)
    assert fresh.access_token == TOKEN and fresh.app_secret == SECRET

    settings.FIELD_ENCRYPTION_KEY = [old]  # and the old key alone can no longer read it
    with pytest.raises(InvalidToken):
        WhatsAppAccount.objects.get(pk=account.pk).access_token  # noqa: B018


def test_rotation_with_a_missing_key_changes_nothing(w, settings):
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    settings.FIELD_ENCRYPTION_KEY = [old]
    account = accounts.add_account(gym=None, **SHARED)
    settings.FIELD_ENCRYPTION_KEY = [new]  # the old key dropped too soon
    with pytest.raises(CommandError, match="Nothing was changed"):
        call_command("rotate_credentials", stdout=io.StringIO())
    settings.FIELD_ENCRYPTION_KEY = [old]
    assert WhatsAppAccount.objects.get(pk=account.pk).access_token == TOKEN


def test_lists_never_decrypt_a_credential(w, settings):
    """A screen showing accounts doesn't need the key: a wrong one can't break the Console's list."""
    c = dumbelo()
    add(c)
    settings.FIELD_ENCRYPTION_KEY = [Fernet.generate_key().decode()]
    assert c.get(ACCOUNTS).status_code == 200


def test_replace_credentials_needs_one_and_checks_again(w):
    c = dumbelo()
    account = add(c)
    WhatsAppAccount.objects.filter(pk=account["id"]).update(status=WhatsAppAccount.WORKING)

    empty = c.post(f"{ACCOUNTS}{account['id']}/replace-credentials/", {}, format="json")
    assert empty.status_code == 400 and "access_token" in empty.json()["error"]["fields"]

    r = c.post(f"{ACCOUNTS}{account['id']}/replace-credentials/", {"access_token": "EAAG-brand-new-token-0000-abcd"}, format="json")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["access_token_last4"] == "abcd" and body["app_secret_last4"] == SECRET[-4:] and body["status"] == "new"
    fresh = WhatsAppAccount.objects.get(pk=account["id"])
    assert fresh.access_token == "EAAG-brand-new-token-0000-abcd" and fresh.app_secret == SECRET
    assert AuditLog.objects.get(action="whatsapp_account.credentials_replaced").after == {"credentials": ["access_token"]}


def test_new_ids_mean_checking_again_and_are_audited(w):
    c = dumbelo()
    account = add(c)
    WhatsAppAccount.objects.filter(pk=account["id"]).update(status=WhatsAppAccount.WORKING)

    r = c.patch(f"{ACCOUNTS}{account['id']}/", {"display_number": "+91 80000 00099"}, format="json")
    assert r.json()["status"] == "working"  # a new display number is only words
    r = c.patch(f"{ACCOUNTS}{account['id']}/", {"phone_number_id": "200000000000077"}, format="json")
    assert r.json()["status"] == "new" and r.json()["phone_number_id"] == "200000000000077"
    changes = AuditLog.objects.filter(action="whatsapp_account.changed").order_by("at", "id")
    assert [a.after["display_number"] for a in changes] == ["+91 80000 00099", "+91 80000 00099"]
    assert changes.last().before["phone_number_id"] == SHARED["phone_number_id"]


# ---- Test Connection ----

def test_test_connection_asks_meta_for_the_number(w, settings):
    settings.WHATSAPP_API_VERSION = "v23.0"
    c = dumbelo()
    account = add(c)
    meta = Meta({"display_phone_number": "+91 80000 00001", "verified_name": "Dumbelo", "quality_rating": "GREEN", "id": "200000000000001"})
    with mock.patch("apps.messages.meta.urlopen", meta):
        r = c.post(f"{ACCOUNTS}{account['id']}/test/")

    assert r.status_code == 200, r.content
    body = r.json()
    assert body["status"] == "working" and body["verified_name"] == "Dumbelo" and body["checked_at"] and body["last_error"] == ""
    [req] = meta.requests
    assert req.full_url.startswith("https://graph.facebook.com/v23.0/200000000000001?fields=")
    assert req.get_method() == "GET" and TOKEN not in req.full_url
    assert req.get_header("Authorization") == f"Bearer {TOKEN}"
    tested = AuditLog.objects.get(action="whatsapp_account.tested")
    assert tested.before == {"status": "new"} and tested.after == {"status": "working"}


def test_a_failed_test_keeps_metas_reason(w):
    c = dumbelo()
    account = add(c)
    error = meta_error(400, {"error": {"message": "Unsupported get request. Object with ID does not exist", "code": 100}})
    with mock.patch("apps.messages.meta.urlopen", Meta(error=error)):
        body = c.post(f"{ACCOUNTS}{account['id']}/test/").json()
    assert body["status"] == "failing" and body["last_error"] == "Unsupported get request. Object with ID does not exist (code 100)"

    with mock.patch("apps.messages.meta.urlopen", Meta(error=URLError("timed out"))):
        body = c.post(f"{ACCOUNTS}{account['id']}/test/").json()
    assert body["status"] == "failing" and body["last_error"] == "Couldn't reach Meta. Try again in a minute."


# ---- A gym's own view ----

def test_a_gyms_admins_see_the_number_they_send_from(w, other):
    c = dumbelo()
    shared = add(c)
    add(c, own(other.gym, 5))  # another gym's own number: never this gym's business
    admin = w.client(w.admin)

    body = admin.get(MINE).json()
    assert body == {"mode": "shared", "number": shared["display_number"], "verified_name": "", "status": "new", "checked_at": None}

    GymBilling.objects.filter(gym=w.gym).update(whatsapp_mode=GymBilling.OWN)
    assert admin.get(MINE).json() == {"mode": "own", "number": None, "verified_name": "", "status": "not_set_up", "checked_at": None}

    mine = add(c, own(w.gym, 6))
    WhatsAppAccount.objects.filter(pk=mine["id"]).update(status=WhatsAppAccount.WORKING, verified_name="Iron House")
    body = admin.get(MINE).json()
    assert body["number"] == mine["display_number"] and body["status"] == "working" and body["verified_name"] == "Iron House"

    GymBilling.objects.filter(gym=w.gym).update(whatsapp_mode=GymBilling.OFF)
    assert admin.get(MINE).json()["status"] == "off" and admin.get(MINE).json()["number"] is None

    for c in [w.client(w.desk), w.client(w.trainer), w.member_client()]:
        assert c.get(MINE).status_code == 403


# ---- Templates ----

def test_templates_say_which_detail_goes_where(w):
    c = dumbelo()
    account = add(c)
    r = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"]}, format="json")
    assert r.status_code == 201, r.content
    t = r.json()
    assert t["kind_label"] == "Plan ending soon" and t["parameters"] == ["first_name", "plan", "gym", "end_date"]
    assert t["category"] == "utility" and t["status"] == "approved"
    assert c.get(ACCOUNTS).json()["results"][0]["template_count"] == 1
    assert c.get(TEMPLATES, {"account": account["id"]}).json()["count"] == 1

    r = c.patch(f"{TEMPLATES}{t['id']}/", {"status": "paused"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "paused"
    assert [a.action for a in AuditLog.objects.filter(action__startswith="whatsapp_template").order_by("at", "id")] == [
        "whatsapp_template.added", "whatsapp_template.changed"]
    assert c.delete(f"{TEMPLATES}{t['id']}/").status_code == 405


def test_a_template_must_match_its_message_and_its_text(w):
    c = dumbelo()
    account = add(c)
    wrong = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "parameters": ["first_name", "amount", "gym", "end_date"]}, format="json")
    assert wrong.status_code == 400 and "amount" in wrong.json()["error"]["fields"]["parameters"][0]

    missing = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "body": "Hi {{1}}, your {{2}} ends soon."}, format="json")
    assert missing.status_code == 400 and "{{1}}, {{2}}, {{3}}, {{4}}" in missing.json()["error"]["fields"]["body"][0]

    twice = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "parameters": ["gym", "gym", "plan", "first_name"]}, format="json")
    assert twice.status_code == 400 and "parameters" in twice.json()["error"]["fields"]

    name = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "name": "Plan Ending!"}, format="json")
    assert name.status_code == 400 and "name" in name.json()["error"]["fields"]


def test_one_approved_template_per_message_and_language(w):
    c = dumbelo()
    account = add(c)
    first = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"]}, format="json").json()

    second = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "name": "plan_ending_v2"}, format="json")
    assert second.status_code == 409 and second.json()["error"]["code"] == "template_approved"

    pending = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "name": "plan_ending_v2", "status": "pending"}, format="json")
    assert pending.status_code == 201
    hindi = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "name": "plan_ending_v2", "language": "hi"}, format="json")
    assert hindi.status_code == 201  # another language is another template

    same_name = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"], "status": "pending"}, format="json")
    assert same_name.status_code == 409 and same_name.json()["error"]["code"] == "template_exists"

    approve = c.patch(f"{TEMPLATES}{pending.json()['id']}/", {"status": "approved"}, format="json")
    assert approve.status_code == 409
    c.patch(f"{TEMPLATES}{first['id']}/", {"status": "disabled"}, format="json")
    assert c.patch(f"{TEMPLATES}{pending.json()['id']}/", {"status": "approved"}, format="json").status_code == 200


def test_a_template_stays_with_its_number(w):
    c = dumbelo()
    account = add(c)
    other_account = add(c, own(w.gym))
    t = c.post(TEMPLATES, {**PLAN_ENDING, "account": account["id"]}, format="json").json()
    r = c.patch(f"{TEMPLATES}{t['id']}/", {"account": other_account["id"]}, format="json")
    assert r.status_code == 400 and "account" in r.json()["error"]["fields"]


def test_the_messages_a_template_can_be_for(w):
    kinds = dumbelo().get(f"{TEMPLATES}kinds/").json()
    assert [k["kind"] for k in kinds] == [k for k, _ in WhatsAppTemplate.KINDS]
    assert len(kinds) == 7
    plan_ending = kinds[0]
    assert plan_ending["label"] == "Plan ending soon"
    assert {"name": "first_name", "label": "Their first name"} in plan_ending["parameters"]


# ---- Query budgets ----

def test_the_lists_keep_a_query_budget(w, other, django_assert_max_num_queries):
    c = dumbelo()
    shared = add(c)
    for i, gym in enumerate([w.gym, other.gym]):
        add(c, own(gym, 7 + i))
    for kind, _ in WhatsAppTemplate.KINDS[:4]:
        params = list(WhatsAppTemplate.PARAMETERS[kind])[:2]
        c.post(TEMPLATES, {"account": shared["id"], "kind": kind, "name": f"{kind}_v1", "body": "{{1}} {{2}}", "parameters": params}, format="json")
    with django_assert_max_num_queries(4):  # auth's user, count, rows
        assert c.get(ACCOUNTS).json()["count"] == 3
    with django_assert_max_num_queries(4):
        assert c.get(TEMPLATES, {"account": shared["id"]}).json()["count"] == 4
