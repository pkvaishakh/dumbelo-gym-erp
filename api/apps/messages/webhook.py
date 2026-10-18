"""Meta's webhook: what happened to the messages we sent, and what people sent back.

Each WhatsApp account has its own address (`/api/whatsapp/webhook/` for Rackline's shared number,
`/api/whatsapp/webhook/<slug>/` for a gym's own) and its own app secret, which signs every call. A call is kept
(`WebhookEvent`) once its signature checks, then handled. Only what belongs to that account's number is touched:
a status moves a message the account sent, a reply opts out the people that number writes to.

Statuses only move forward (sent → delivered → read); a repeated or late one changes nothing. Usage is counted
from `delivered_at`, so Meta repeating "delivered" can't bill a message twice.
"""
import hashlib
import hmac
import json
import logging
import re
from datetime import UTC, datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import normalize_phone
from apps.audit.models import record
from apps.members.models import Member

from .models import InboundMessage, Message, WebhookEvent, WhatsAppAccount

log = logging.getLogger(__name__)

#: What counts as asking us to stop, once spaces, punctuation and case are set aside.
STOP_WORDS = {"stop", "stopall", "unsubscribe"}


def signed(account: WhatsAppAccount, body: bytes, header: str) -> bool:
    """True when `X-Hub-Signature-256` (`sha256=<hex>`) is the body's HMAC under the account's app secret."""
    if not header.startswith("sha256=") or not account.app_secret:
        return False
    expected = hmac.new(account.app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(header.removeprefix("sha256="), expected)


def verified(account: WhatsAppAccount, mode: str, token: str) -> bool:
    """Meta's handshake when the webhook is set up: it sends back the verify token shown in the Console."""
    return mode == "subscribe" and bool(token) and hmac.compare_digest(token, account.verify_token)


def receive(account: WhatsAppAccount, body: bytes) -> WebhookEvent:
    """Keep a signed call as it came, then handle it."""
    event = WebhookEvent.objects.create(account=account, body=body.decode("utf-8", errors="replace"))
    return process(event)


def process(event: WebhookEvent) -> WebhookEvent:
    """Handle a kept call, the first time or again. A call that can't be handled keeps the reason, and this never
    raises: Meta must still hear 200, or it sends the same call again for days.

    Safe to repeat: statuses only move forward and a reply is kept (and acted on) once, so running a call again
    only does what it couldn't do the first time, such as a status that came before the send saved Meta's id."""
    event.error = ""
    try:
        with transaction.atomic():
            handle(event.account, json.loads(event.body))
    except Exception as e:
        log.exception("Webhook event %s for account %s couldn't be handled", event.pk, event.account_id)
        event.error = (f"{e.__class__.__name__}: {e}")[:200]
    event.processed_at = timezone.now()
    event.save(update_fields=["processed_at", "error", "updated_at"])
    return event


def replay(events) -> dict[str, int]:
    """Handle kept calls again, oldest first (`manage.py replay_webhook_events`). Says how many went through and
    how many still couldn't be handled."""
    counts = {"handled": 0, "failed": 0}
    for event in events.select_related("account").order_by("created_at", "id").iterator(chunk_size=500):
        counts["failed" if process(event).error else "handled"] += 1
    return counts


def handle(account: WhatsAppAccount, payload: dict) -> None:
    """Every status and incoming message in one call, for this account's number only."""
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            if change.get("field") != "messages" or (value.get("metadata") or {}).get("phone_number_id") != account.phone_number_id:
                continue  # another number's, or something other than messages: not ours to act on
            for status in value.get("statuses") or []:
                update_status(account, status)
            for message in value.get("messages") or []:
                take_inbound(account, message)


def _at(timestamp) -> datetime:
    """Meta's times are Unix seconds, which are UTC."""
    return datetime.fromtimestamp(int(timestamp), tz=UTC)


def _reason(errors: list) -> tuple[str, str]:
    """Meta's code and its words for why a message failed ("Message undeliverable (code 131026)")."""
    error = (errors or [{}])[0]
    code = str(error.get("code") or "")
    words = (error.get("error_data") or {}).get("details") or error.get("message") or error.get("title") or "Meta couldn't deliver it"
    return (f"{words} (code {code})" if code else words)[:200], code[:16]


def update_status(account: WhatsAppAccount, status: dict) -> int:
    """Move the message Meta's status is about, if this account sent it and the status is ahead of where it is.
    Says how many rows changed (0 or 1). One conditional update: two calls at once can't both move it.

    A status for a message whose send hasn't saved Meta's id yet finds nothing; `replay` runs its call again."""
    meta_id, word = str(status.get("id") or ""), status.get("status")
    if not meta_id or word not in (Message.SENT, Message.DELIVERED, Message.READ, Message.FAILED):
        return 0
    at = _at(status["timestamp"])
    rows = Message.objects.filter(account=account, provider_id=meta_id, status__in=Message.moves_to(word))
    change = {"status": word, "updated_at": timezone.now()}
    if word == Message.FAILED:
        change["error"], change["error_code"] = _reason(status.get("errors"))
    if word in (Message.DELIVERED, Message.READ):  # read without a delivered first still reached the phone
        change["delivered_at"] = Coalesce("delivered_at", at)
    if word == Message.READ:
        change["read_at"] = at
    return rows.update(**change)


def _text(message: dict) -> str:
    kind = message.get("type")
    if kind == "text":
        return (message.get("text") or {}).get("body") or ""
    if kind == "button":  # a quick-reply button on a template
        return (message.get("button") or {}).get("text") or ""
    if kind == "interactive":
        reply = message.get("interactive") or {}
        return (reply.get("button_reply") or reply.get("list_reply") or {}).get("title") or ""
    return ""


def is_stop(text: str) -> bool:
    return re.sub(r"[\W_]+", "", text).lower() in STOP_WORDS


def take_inbound(account: WhatsAppAccount, message: dict) -> InboundMessage | None:
    """Keep what someone sent the number, once. STOP opts them out of every message the number sends them."""
    sender = "+" + re.sub(r"\D", "", str(message.get("from") or ""))[:15]
    text = _text(message)
    inbound = InboundMessage(account=account, meta_id=str(message["id"])[:128], from_number=sender,
                             kind=str(message.get("type") or "")[:20], text=text, received_at=_at(message["timestamp"]),
                             is_stop=is_stop(text))
    try:
        with transaction.atomic():
            inbound.save()
    except IntegrityError:
        return None  # Meta sent it before: already kept, and already acted on
    if inbound.is_stop:
        opt_out(account, inbound)
    return inbound


def opt_out(account: WhatsAppAccount, inbound: InboundMessage) -> list[Member]:
    """The members this number writes to on the number that said STOP: on a gym's own number, that gym's member;
    on the shared number, the member in every gym that has messaged them from it. Audited, so the desk can see why."""
    try:
        phone = normalize_phone(inbound.from_number)
    except ValidationError:  # not an Indian mobile: no member has it
        return []
    members = Member.objects.filter(phone=phone, reminders_opted_out=False)
    if account.is_shared:
        members = members.filter(messages__account=account).distinct()
    else:
        members = members.filter(gym_id=account.gym_id)
    members = list(members.select_related("gym"))
    for member in members:
        member.reminders_opted_out = True
        member.save(update_fields=["reminders_opted_out", "updated_at"])
        record(None, "member.opted_out", member, {"reminders_opted_out": False},
               {"reminders_opted_out": True, "by": "WhatsApp reply", "text": inbound.text[:40]}, gym=member.gym)
    inbound.opted_out.add(*members)
    return members
