"""Meta's webhook: the handshake, signatures, delivery statuses, STOP replies, and usage on the invoice."""
import hashlib
import hmac
import io
import json
from datetime import UTC, date, datetime

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.billing import invoicing
from apps.billing.models import InvoiceLine
from apps.members.models import Member
from apps.messages import accounts
from apps.messages.models import InboundMessage, Message, WebhookEvent, WhatsAppAccount
from apps.messages.services import send_due
from apps.messages.usage import usage
from apps.reminders.services import queue_for
from tests.test_invoices import MONTH

SHARED_SECRET = "shared-test-app-secret-00"  # conftest's shared number
SHARED_NUMBER_ID = "200000000000009"
OWN = {"waba_id": "100000000000002", "phone_number_id": "200000000000002", "display_number": "+91 80000 00002",
       "access_token": "EAAGown-number-token-1111111111", "app_secret": "own-number-app-secret-11"}
OCT_10 = datetime(2026, 10, 10, 6, 30, tzinfo=UTC)


def ts(at: datetime) -> str:
    return str(int(at.timestamp()))


def status(meta_id, word, at=OCT_10, **extra):
    return {"id": meta_id, "status": word, "timestamp": ts(at), "recipient_id": "919800000001", **extra}


def inbound(text, meta_id="wamid.IN1", sender="919800000001", kind="text"):
    body = {"text": {"body": text}} if kind == "text" else {"button": {"text": text, "payload": text}}
    return {"from": sender, "id": meta_id, "timestamp": ts(OCT_10), "type": kind, **body}


def event(statuses=(), messages=(), number_id=SHARED_NUMBER_ID) -> bytes:
    value = {"messaging_product": "whatsapp", "metadata": {"display_phone_number": "918000000009", "phone_number_id": number_id}}
    if statuses:
        value["statuses"] = list(statuses)
    if messages:
        value["messages"] = list(messages)
    payload = {"object": "whatsapp_business_account", "entry": [{"id": "100000000000009", "changes": [{"field": "messages", "value": value}]}]}
    return json.dumps(payload).encode()


def sign(body: bytes, secret=SHARED_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post(client, body: bytes, secret=SHARED_SECRET, url=None, signature=None):
    headers = {} if signature is False else {"HTTP_X_HUB_SIGNATURE_256": sign(body, secret) if signature is None else signature}
    return client.post(url or reverse("whatsapp-webhook"), body, content_type="application/json", **headers)


def own_account(gym) -> WhatsAppAccount:
    return accounts.add_account(gym=gym, **OWN)


def sent(w, account, meta_id="wamid.OUT1", billable=True, rate=15, member=None, key=None) -> Message:
    """A message that went out from `account` and that Meta has taken (status sent, Meta's id kept)."""
    member = member or w.member
    template = account.templates.filter(kind="payment_due").first()
    return Message.objects.create(
        gym=member.gym, member=member, kind="dues", dedupe_key=key or f"test:{meta_id}", account=account, template=template,
        to=member.phone, text="Hi", for_date=date(2026, 10, 10), status=Message.SENT, attempts=1, provider="whatsapp_cloud",
        provider_id=meta_id, billable=billable, rate_paise=rate if billable else 0,
    )


def same_phone(world, member) -> Member:
    """The same person, as a member of another gym."""
    return Member.objects.create(gym=world.gym, code="M-SAME", name=member.name, phone=member.phone, home_branch=world.a)


@pytest.fixture
def meta(client):
    """Meta calling the shared number's webhook with the given statuses and replies, signed as Meta signs them."""
    def call(statuses=(), messages=(), **kwargs):
        r = post(client, event(statuses, messages), **kwargs)
        assert r.status_code == 200, r.content
        return r
    return call


# The handshake

def test_the_verification_handshake_answers_metas_challenge(w, client, shared_number):
    params = {"hub.mode": "subscribe", "hub.verify_token": shared_number.verify_token, "hub.challenge": "1158201444"}
    r = client.get(reverse("whatsapp-webhook"), params)
    assert r.status_code == 200 and r.content == b"1158201444" and r["Content-Type"].startswith("text/plain")


def test_a_gyms_own_number_has_its_own_handshake(w, client, shared_number):
    own = own_account(w.gym)
    url = reverse("whatsapp-webhook-own", args=[own.webhook_slug])
    ok = client.get(url, {"hub.mode": "subscribe", "hub.verify_token": own.verify_token, "hub.challenge": "42"})
    assert ok.status_code == 200 and ok.content == b"42"
    shared_token = client.get(url, {"hub.mode": "subscribe", "hub.verify_token": shared_number.verify_token, "hub.challenge": "42"})
    assert shared_token.status_code == 403  # another number's token doesn't open this one


@pytest.mark.parametrize("params", [
    {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1"},
    {"hub.mode": "subscribe", "hub.challenge": "1"},
    {"hub.mode": "unsubscribe", "hub.verify_token": "{token}", "hub.challenge": "1"},
])
def test_a_wrong_verify_token_is_refused(w, client, shared_number, params):
    params = {k: v.replace("{token}", shared_number.verify_token) for k, v in params.items()}
    r = client.get(reverse("whatsapp-webhook"), params)
    assert r.status_code == 403 and r.json()["error"]["code"] == "bad_verify_token"


def test_an_address_that_isnt_a_gyms_number_answers_404(w, client, shared_number):
    assert client.get("/api/whatsapp/webhook/nope/", {"hub.mode": "subscribe"}).status_code == 404
    assert post(client, event(), url="/api/whatsapp/webhook/nope/").status_code == 404
    # the shared number's own slug isn't an address: it has the plain one
    assert post(client, event(), url=f"/api/whatsapp/webhook/{shared_number.webhook_slug}/").status_code == 404


# Signatures

@pytest.mark.parametrize("signature", [False, "", "sha256=", "sha256=" + "0" * 64, "md5=abc", "not-even-close"])
def test_a_bad_or_missing_signature_is_refused_and_nothing_is_kept(w, client, shared_number, signature):
    msg = sent(w, shared_number)
    r = post(client, event([status(msg.provider_id, "delivered")]), signature=signature)
    assert r.status_code == 403 and r.json()["error"]["code"] == "bad_signature"
    assert not WebhookEvent.objects.exists()
    msg.refresh_from_db()
    assert msg.status == Message.SENT


def test_a_call_signed_with_another_numbers_secret_is_refused(w, client, shared_number):
    own_account(w.gym)
    assert post(client, event(), secret=OWN["app_secret"]).status_code == 403


def test_a_body_changed_after_signing_is_refused(w, client, shared_number):
    body = event()
    signature = sign(body)
    assert post(client, body.replace(b"whatsapp", b"WHATSAPP", 1), signature=signature).status_code == 403


def test_a_signed_call_is_kept_as_it_came_and_answered_200(w, client, shared_number):
    body = event([status("wamid.unknown", "delivered")])
    r = post(client, body)
    assert r.status_code == 200
    kept = WebhookEvent.objects.get()
    assert kept.account == shared_number and kept.body == body.decode() and kept.processed_at and kept.error == ""


def test_a_call_that_cant_be_handled_is_still_kept_and_answered_200(w, client, shared_number):
    r = post(client, b"{not json")
    assert r.status_code == 200
    kept = WebhookEvent.objects.get()
    assert kept.body == "{not json" and kept.error.startswith("JSONDecodeError")


def test_one_bad_status_doesnt_half_apply_a_call(w, meta, shared_number):
    first = sent(w, shared_number, "wamid.A")
    meta([status("wamid.A", "delivered"), {"id": "wamid.B", "status": "delivered"}])  # the second has no time
    first.refresh_from_db()
    assert first.status == Message.SENT  # the call is kept with its error, to look at, rather than half done
    assert WebhookEvent.objects.get().error.startswith("KeyError")


# Statuses

def test_statuses_move_a_message_forward_with_metas_utc_times(w, meta, shared_number):
    msg = sent(w, shared_number)
    delivered_at, read_at = datetime(2026, 10, 10, 6, 31, 5, tzinfo=UTC), datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
    meta([status(msg.provider_id, "sent")])
    meta([status(msg.provider_id, "delivered", delivered_at)])
    msg.refresh_from_db()
    assert msg.status == Message.DELIVERED and msg.delivered_at == delivered_at and msg.read_at is None
    meta([status(msg.provider_id, "read", read_at)])
    msg.refresh_from_db()
    assert msg.status == Message.READ and msg.delivered_at == delivered_at and msg.read_at == read_at


def test_a_delivered_after_read_is_ignored(w, meta, shared_number):
    msg = sent(w, shared_number)
    read_at = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
    meta([status(msg.provider_id, "read", read_at)])
    meta([status(msg.provider_id, "delivered", datetime(2026, 10, 10, 8, 0, tzinfo=UTC))])
    msg.refresh_from_db()
    # read means it reached the phone, so it counts as delivered, at the time Meta first said so
    assert msg.status == Message.READ and msg.read_at == read_at and msg.delivered_at == read_at


def test_a_repeated_delivered_counts_once(w, meta, shared_number):
    msg = sent(w, shared_number)
    first = datetime(2026, 10, 10, 6, 31, tzinfo=UTC)
    meta([status(msg.provider_id, "delivered", first)])
    meta([status(msg.provider_id, "delivered", datetime(2026, 10, 12, 6, 31, tzinfo=UTC))])
    meta([status(msg.provider_id, "delivered", first), status(msg.provider_id, "delivered", first)])
    msg.refresh_from_db()
    assert msg.delivered_at == first
    assert usage(w.gym, date(2026, 10, 1), date(2026, 10, 31)) == [
        {"category": "utility", "rate_paise": 15, "messages": 1, "amount_paise": 15},
    ]


def test_failed_keeps_metas_code_and_reason(w, meta, shared_number):
    msg = sent(w, shared_number)
    error = {"code": 131026, "title": "Message undeliverable", "message": "Message undeliverable",
             "error_data": {"details": "Message could not be delivered to the recipient"}}
    meta([status(msg.provider_id, "failed", errors=[error])])
    msg.refresh_from_db()
    assert msg.status == Message.FAILED and msg.error_code == "131026"
    assert msg.error == "Message could not be delivered to the recipient (code 131026)"
    meta([status(msg.provider_id, "delivered")])  # failed is final
    msg.refresh_from_db()
    assert msg.status == Message.FAILED and msg.delivered_at is None


def test_failed_after_delivered_is_ignored(w, meta, shared_number):
    msg = sent(w, shared_number)
    meta([status(msg.provider_id, "delivered")])
    meta([status(msg.provider_id, "failed", errors=[{"code": 131000, "title": "Something went wrong"}])])
    msg.refresh_from_db()
    assert msg.status == Message.DELIVERED and msg.error == ""


def test_a_status_for_another_accounts_message_changes_nothing(w, other, client, shared_number):
    own = own_account(other.gym)
    theirs = sent(other, own, meta_id="wamid.SAME")
    ours = sent(w, shared_number, meta_id="wamid.OURS")
    # The shared number's call names the other number's message id: it isn't the shared number's to change
    post(client, event([status("wamid.SAME", "read")]))
    # A gym's own address, signed with its own secret, but carrying another number's update
    url = reverse("whatsapp-webhook-own", args=[own.webhook_slug])
    post(client, event([status("wamid.OURS", "read")], number_id=SHARED_NUMBER_ID), secret=OWN["app_secret"], url=url)
    post(client, event([status("wamid.OURS", "read")], number_id=own.phone_number_id), secret=OWN["app_secret"], url=url)
    theirs.refresh_from_db()
    ours.refresh_from_db()
    assert theirs.status == ours.status == Message.SENT


def test_a_gyms_own_number_updates_its_own_messages(w, client, shared_number):
    own = own_account(w.gym)
    msg = sent(w, own, billable=False)
    url = reverse("whatsapp-webhook-own", args=[own.webhook_slug])
    r = post(client, event([status(msg.provider_id, "delivered")], number_id=own.phone_number_id), secret=OWN["app_secret"], url=url)
    assert r.status_code == 200
    msg.refresh_from_db()
    assert msg.status == Message.DELIVERED
    assert usage(w.gym, date(2026, 10, 1), date(2026, 10, 31)) == []  # the gym pays Meta itself for its own number


def test_statuses_follow_a_message_sent_by_the_daily_job(w, meta, shared_number):
    member = w.plan_ending_on(w.today, "Ravi", "9811111117")
    queue_for(w.gym, w.today)
    assert send_due(w.gym, w.today)["sent"] == 1
    msg = Message.objects.get(member=member)
    meta([status(msg.provider_id, "delivered")])
    msg.refresh_from_db()
    assert msg.status == Message.DELIVERED


# Replies and STOP

@pytest.mark.parametrize("text", ["STOP", "stop", " Stop. ", "STOP ALL", "Unsubscribe"])
def test_a_member_replying_stop_is_opted_out(w, meta, shared_number, text):
    sent(w, shared_number)
    meta(messages=[inbound(text)])
    w.member.refresh_from_db()
    assert w.member.reminders_opted_out
    reply = InboundMessage.objects.get()
    assert reply.is_stop and reply.from_number == "+919800000001" and reply.text == text and list(reply.opted_out.all()) == [w.member]
    log = AuditLog.objects.get(action="member.opted_out")
    assert log.gym == w.gym and log.object_id == str(w.member.pk) and log.actor is None


def test_a_stop_button_opts_out_too(w, meta, shared_number):
    sent(w, shared_number)
    meta(messages=[inbound("Stop", kind="button")])
    w.member.refresh_from_db()
    assert w.member.reminders_opted_out


@pytest.mark.parametrize("text", ["Thanks!", "stop sending me the dues one", "Don't stop"])
def test_other_replies_are_kept_but_change_nothing(w, meta, shared_number, text):
    sent(w, shared_number)
    meta(messages=[inbound(text)])
    w.member.refresh_from_db()
    assert not w.member.reminders_opted_out
    assert InboundMessage.objects.get().text == text and not AuditLog.objects.filter(action="member.opted_out").exists()


def test_the_same_reply_twice_is_kept_once(w, meta, shared_number):
    sent(w, shared_number)
    meta(messages=[inbound("STOP")])
    meta(messages=[inbound("STOP")])
    assert InboundMessage.objects.count() == 1 and AuditLog.objects.filter(action="member.opted_out").count() == 1


def test_stop_on_the_shared_number_reaches_only_gyms_that_messaged_them_from_it(w, other, meta, shared_number):
    sent(w, shared_number)
    same_person = same_phone(other, w.member)  # the same phone, at a gym that never messaged her
    meta(messages=[inbound("STOP")])
    w.member.refresh_from_db()
    same_person.refresh_from_db()
    assert w.member.reminders_opted_out and not same_person.reminders_opted_out


def test_stop_on_a_gyms_own_number_opts_out_that_gyms_member_only(w, other, client, shared_number):
    own = own_account(w.gym)
    same_person = same_phone(other, w.member)
    sent(other, shared_number, member=same_person)
    url = reverse("whatsapp-webhook-own", args=[own.webhook_slug])
    post(client, event(messages=[inbound("STOP")], number_id=own.phone_number_id), secret=OWN["app_secret"], url=url)
    w.member.refresh_from_db()
    same_person.refresh_from_db()
    assert w.member.reminders_opted_out and not same_person.reminders_opted_out


def test_an_opted_out_member_gets_no_more_reminders(w, meta, shared_number):
    member = w.plan_ending_on(w.today, "Ravi", "9811111117")
    sent(w, shared_number, member=member, key="earlier")
    meta(messages=[inbound("STOP", sender="919811111117")])
    queue_for(w.gym, w.today)
    assert send_due(w.gym, w.today) == {"sent": 0, "failed": 0, "skipped": 1}


# Usage on the invoice

def deliver_at(meta, msg, at):
    meta([status(msg.provider_id, "delivered", at)])


def test_usage_on_an_invoice_matches_the_delivered_messages(w, other, meta, shared_number):
    """Billing day 1: the 1 Nov invoice bills October's messages, by the gym's clock (India, UTC+5:30)."""
    in_october = [sent(w, shared_number, f"wamid.OCT{i}") for i in range(3)]
    for msg in in_october:
        deliver_at(meta, msg, datetime(2026, 10, 15, 4, 0, tzinfo=UTC))
    read_only = sent(w, shared_number, "wamid.READ")  # its delivered never came: read says it got there
    meta([status(read_only.provider_id, "read", datetime(2026, 10, 20, 4, 0, tzinfo=UTC))])
    first_minute = sent(w, shared_number, "wamid.FIRST")  # 1 Oct 00:00 IST
    deliver_at(meta, first_minute, datetime(2026, 9, 30, 18, 30, tzinfo=UTC))
    last_minute = sent(w, shared_number, "wamid.LAST")  # 31 Oct 23:59 IST
    deliver_at(meta, last_minute, datetime(2026, 10, 31, 18, 29, tzinfo=UTC))
    marketing_rate = sent(w, shared_number, "wamid.DEAR", rate=90)
    deliver_at(meta, marketing_rate, datetime(2026, 10, 16, 4, 0, tzinfo=UTC))

    september = sent(w, shared_number, "wamid.SEP")  # 30 Sep 23:59 IST: last month's invoice had it
    deliver_at(meta, september, datetime(2026, 9, 30, 18, 29, tzinfo=UTC))
    november = sent(w, shared_number, "wamid.NOV")  # 1 Nov 00:00 IST: next month's
    deliver_at(meta, november, datetime(2026, 10, 31, 18, 30, tzinfo=UTC))
    sent(w, shared_number, "wamid.NEVER")  # sent, never delivered: costs nothing
    failed = sent(w, shared_number, "wamid.FAIL")
    meta([status(failed.provider_id, "failed", errors=[{"code": 131026}])])
    sent(w, shared_number, "wamid.FREE", billable=False)  # not billable: as if from the gym's own number
    theirs = sent(other, shared_number, "wamid.THEIRS")  # another gym's message is on another gym's invoice
    deliver_at(meta, theirs, datetime(2026, 10, 15, 4, 0, tzinfo=UTC))

    inv = invoicing.write_invoice(w.gym, date(2026, 11, 1))
    lines = list(inv.lines.filter(kind=InvoiceLine.WHATSAPP_USAGE).values_list("description", "quantity", "rate_paise", "amount_paise", "starts", "ends"))
    assert lines == [
        ("WhatsApp messages delivered (utility), 1 Oct to 31 Oct", 6, 15, 90, date(2026, 10, 1), date(2026, 10, 31)),
        ("WhatsApp messages delivered (utility), 1 Oct to 31 Oct", 1, 90, 90, date(2026, 10, 1), date(2026, 10, 31)),
    ]
    delivered = Message.objects.filter(gym=w.gym, billable=True, delivered_at__gte=datetime(2026, 9, 30, 18, 30, tzinfo=UTC),
                                       delivered_at__lt=datetime(2026, 10, 31, 18, 30, tzinfo=UTC))
    assert sum(q for _, q, *_ in lines) == delivered.count() == 7
    assert inv.total_paise == MONTH + 6 * 15 + 90


def test_a_month_without_delivered_messages_has_no_usage_line(w, shared_number):
    sent(w, shared_number)  # sent in October, never delivered
    inv = invoicing.write_invoice(w.gym, date(2026, 11, 1))
    assert not inv.lines.filter(kind=InvoiceLine.WHATSAPP_USAGE).exists()


def test_usage_follows_the_gyms_billing_month(w, meta, shared_number):
    """Billing day 15: the 15 Nov invoice bills 15 Oct to 14 Nov."""
    inside = sent(w, shared_number, "wamid.IN")
    deliver_at(meta, inside, datetime(2026, 10, 14, 18, 30, tzinfo=UTC))  # 15 Oct 00:00 IST
    before = sent(w, shared_number, "wamid.BEFORE")
    deliver_at(meta, before, datetime(2026, 10, 14, 18, 29, tzinfo=UTC))
    line = invoicing.whatsapp_usage_lines(w.billing, date(2026, 11, 15))
    assert [(x.quantity, x.starts, x.ends, x.description) for x in line] == [
        (1, date(2026, 10, 15), date(2026, 11, 14), "WhatsApp messages delivered (utility), 15 Oct to 14 Nov"),
    ]


# Running kept calls again

def replay(*args) -> str:
    out = io.StringIO()
    call_command("replay_webhook_events", *args, stdout=out)
    return out.getvalue()


def test_a_status_before_the_send_saved_metas_id_lands_when_run_again(w, meta, shared_number):
    msg = sent(w, shared_number, meta_id="")  # Meta has taken it, but our send hasn't saved the id yet
    meta([status("wamid.EARLY", "delivered", datetime(2026, 10, 10, 6, 31, tzinfo=UTC))])
    msg.provider_id = "wamid.EARLY"
    msg.save(update_fields=["provider_id"])
    msg.refresh_from_db()
    assert msg.status == Message.SENT  # the early status found nothing

    event = WebhookEvent.objects.get()
    assert replay("--id", str(event.pk)) == "1 call run again: 1 handled, 0 still failing.\n"
    msg.refresh_from_db()
    assert msg.status == Message.DELIVERED and msg.delivered_at == datetime(2026, 10, 10, 6, 31, tzinfo=UTC)
    replay("--id", str(event.pk))  # and again: nothing more
    assert usage(w.gym, date(2026, 10, 1), date(2026, 10, 31))[0]["messages"] == 1


def test_running_a_stop_again_opts_out_once(w, meta, shared_number):
    sent(w, shared_number)
    meta(messages=[inbound("STOP")])
    replay("--since", "2026-01-01")
    assert InboundMessage.objects.count() == 1 and AuditLog.objects.filter(action="member.opted_out").count() == 1


def test_failed_runs_only_the_calls_that_couldnt_be_handled(w, client, meta, shared_number):
    msg = sent(w, shared_number)
    post(client, b"{not json")
    meta([status(msg.provider_id, "delivered")])
    assert replay("--since", "2026-01-01", "--failed") == "1 call run again: 0 handled, 1 still failing.\n"
    assert replay("--since", "2026-01-01") == "2 calls run again: 1 handled, 1 still failing.\n"


def test_since_leaves_out_older_calls(w, meta, shared_number):
    meta()
    WebhookEvent.objects.update(created_at=datetime(2026, 10, 1, 3, 0, tzinfo=UTC))  # 1 Oct 08:30 IST
    assert replay("--since", "2026-10-01T09:00+05:30").startswith("0 calls")
    assert replay("--since", "2026-10-01T08:00+05:30").startswith("1 call ")
    assert replay("--since", "2026-10-01").startswith("1 call ")  # a bare day is from its midnight, UTC


@pytest.mark.parametrize("args, message", [((), "Say which calls"), (("--since", "yesterday"), "Give --since as")])
def test_the_command_says_what_it_needs(w, args, message):
    with pytest.raises(CommandError, match=message):
        replay(*args)
