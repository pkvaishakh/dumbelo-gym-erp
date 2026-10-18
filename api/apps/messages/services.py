"""Sending WhatsApp messages, and turning today's reminder list into them.

Every message follows the same three steps: its row is written as queued (under a key unique in the gym, so it
can't be written twice), then it is sent, then Meta's id is kept. A row is counted as an attempt *before* it is
handed over, so a crash in between leaves it looking tried, not untried: it is never sent again on its own. Meta
saying "not now" (rate limits, Meta busy) is tried again up to 3 times, with growing waits (`send_retries`, every
minute); anything else fails at once. One failure never stops the rest.

`apps.reminders` works out who has earned a nudge; `send_due` sends it. The rules are the gym's: one message a
member a day, nothing to someone who asked us to stop, nothing while the gym has reminders off, WhatsApp off, or
its account paused.
"""
from datetime import date, datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.billing.models import GymBilling
from apps.core import clock
from apps.core.money import rupees
from apps.gyms.models import Gym
from apps.members.models import Member
from apps.reminders.models import ReminderDue

from .accounts import account_for, approved_templates, whatsapp_mode
from .models import Message, WhatsAppAccount, WhatsAppTemplate
from .senders import Sender, SendFailed, get_sender

#: Which reminder a member hears about when they have earned more than one: the plan that runs out today
#: first, then money owed, then the earlier warnings. Everything else can wait for tomorrow's message.
PRIORITY = [ReminderDue.EXPIRING_0, ReminderDue.DUES, ReminderDue.EXPIRING_3, ReminderDue.EXPIRING_7]

#: How long to wait before trying again after each temporary failure: 3 retries, then it has failed.
RETRY_WAITS = (timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=15))
#: A row still "sending" this long after its attempt began was cut off mid-send (the worker died).
INTERRUPTED_AFTER = timedelta(hours=1)
RETRY_BATCH = 500

PAUSED = "Not sent: your gym's Rackline account is paused."
OFF = "Not sent: WhatsApp messages are off for your gym."
NOT_SET_UP = "Not sent: WhatsApp isn't set up for your gym yet."
OPTED_OUT = "Not sent: they asked not to get messages."
INTERRUPTED = "Sending stopped part-way, so it may or may not have gone. It won't be sent again on its own."


def stop_reason(gym: Gym, member: Member | None = None) -> str | None:
    """Why nothing may go out from this gym (or to this member) right now; None when it may."""
    if gym.is_suspended:
        return PAUSED
    if whatsapp_mode(gym) == GymBilling.OFF:
        return OFF
    if member is not None and member.reminders_opted_out:
        return OPTED_OUT
    return None


class Route:
    """The number a gym's messages go from (by its WhatsApp mode) and that number's approved templates, read once
    for a whole run."""

    def __init__(self, gym: Gym):
        approved = approved_templates(gym)
        # Usually one query: the account comes with its templates. Only a number without any is looked up alone.
        self.account: WhatsAppAccount | None = approved[0].account if approved else account_for(gym)
        self.templates: dict[str, WhatsAppTemplate] = {}
        for template in approved:
            self.templates.setdefault(template.kind, template)  # one language a kind for now: the first
        self.billing = getattr(gym, "billing", None)

    def fill_in(self, row: Message, values: dict[str, str]) -> None:
        """Put the number, the template and the words on an unsaved row, ready to send. When it can't go, mark it
        failed and say why, so the desk sees the reason rather than nothing."""
        if self.account is None:
            return _cant(row, NOT_SET_UP)
        row.account = self.account
        kind = Message.TEMPLATE_KIND[row.kind]
        template = self.templates.get(kind)
        if template is None:
            label = dict(WhatsAppTemplate.KINDS)[kind].lower()
            return _cant(row, f"Not sent: there's no approved WhatsApp template for {label} yet.")
        if missing := [name for name in template.parameters if not values.get(name)]:
            labels = WhatsAppTemplate.PARAMETERS[kind]
            return _cant(row, f"Not sent: it's missing {', '.join(labels.get(m, m).lower() for m in missing)}."[:200])
        row.template, row.parameters = template, [values[name] for name in template.parameters]
        row.text = template.fill(row.parameters)
        if self.account.is_shared:  # the gym's own number is paid to Meta by the gym, not through Rackline
            row.billable = True
            row.rate_paise = getattr(self.billing, f"{template.category}_message_paise", 0)
        row.attempts = 1  # claimed by whoever writes it: see the module's docstring


def _cant(row: Message, reason: str) -> None:
    row.status, row.error = Message.FAILED, reason


def _failed(row: Message, error: str, code: str, temporary: bool, now: datetime) -> None:
    row.error, row.error_code = (error or "It didn't go")[:200], code[:16]
    if temporary and row.attempts <= len(RETRY_WAITS):
        row.status, row.next_retry_at = Message.QUEUED, now + RETRY_WAITS[row.attempts - 1]
    else:
        row.status, row.next_retry_at = Message.FAILED, None


def deliver(row: Message, sender: Sender, now: datetime | None = None) -> Message:
    """Hand a queued row, already counted as an attempt, to the sender, and keep what happened."""
    now = now or timezone.now()
    try:
        row.provider_id = sender.send_message(row)
    except SendFailed as e:
        _failed(row, str(e), e.code, e.temporary, now)
    except Exception as e:
        # Anything the provider's own client raises is this message's failure, not the run's. Not retried: we
        # can't tell whether it went.
        _failed(row, str(e) or e.__class__.__name__, "", False, now)
    else:
        row.status, row.next_retry_at, row.error, row.error_code = Message.SENT, None, "", ""
    row.provider = sender.name
    # Saved one at a time, not in bulk: a message that has gone out must be on record even if the run dies next.
    row.save(update_fields=["status", "provider", "provider_id", "error", "error_code", "next_retry_at", "updated_at"])
    return row


def queue(rows: list[Message]) -> bool:
    """Write new rows in one go. False when another run already wrote one of them: it is sending them, so this
    run sends nothing. Writing them is what claims them (each key is unique in its gym)."""
    try:
        with transaction.atomic():
            Message.objects.bulk_create(rows, batch_size=500)
    except IntegrityError:
        return False
    return True


# ---- Reminders ----

def plan_label(sub) -> str:
    """'Monthly plan' — the plan's name with the word plan, unless the gym already named it that."""
    if sub is None:
        return "membership"
    name = sub.plan.name.strip()
    return name if name.lower().endswith(("plan", "membership", "pack")) else f"{name} plan"


def reminder_values(gym: Gym, member: Member, kind: str, for_date: date) -> dict[str, str]:
    """Every detail a reminder's template can use (WhatsAppTemplate.PARAMETERS), by name."""
    first = member.name.split()[0] if member.name.split() else member.name
    sub = member.current_subscription(for_date)
    values = {"first_name": first, "plan": plan_label(sub), "gym": gym.name}
    if kind == ReminderDue.DUES:
        values["amount"] = rupees(member.balance_paise())
    elif sub is not None:
        days = (sub.ends - for_date).days
        values["end_date"] = clock.date_label(sub.ends)
        values["days_left"] = "tomorrow" if days == 1 else f"in {days} days"
    return values


def _one_kind_per_member(gym: Gym, for_date: date) -> dict[int, str]:
    """The single reminder each member is owed today, by member id (see PRIORITY)."""
    rank = {kind: i for i, kind in enumerate(PRIORITY)}
    best: dict[int, str] = {}
    for member_id, kind in ReminderDue.objects.filter(gym=gym, for_date=for_date).values_list("member_id", "kind"):
        if member_id not in best or rank.get(kind, len(rank)) < rank.get(best[member_id], len(rank)):
            best[member_id] = kind
    return best


def send_due(gym: Gym, for_date: date) -> dict[str, int]:
    """Send the gym's reminders for one local day. Says how many went and how many didn't ("failed" includes
    any waiting to be tried again).

    Safe to run again: the day's messages are already on record, so a second run sends nothing.
    """
    counts = {"sent": 0, "failed": 0, "skipped": 0}
    if not gym.reminders_on or stop_reason(gym):
        return counts
    wanted = _one_kind_per_member(gym, for_date)
    keys = {member_id: Message.reminder_key(member_id, for_date) for member_id in wanted}
    already = set(Message.objects.filter(gym=gym, dedupe_key__in=keys.values()).values_list("dedupe_key", flat=True)) if keys else set()
    todo = {member_id: kind for member_id, kind in wanted.items() if keys[member_id] not in already}
    if not todo:
        return counts
    # with_totals() brings the balance and the current plan the words need, for every member in two queries
    members = Member.objects.filter(gym=gym, id__in=todo, is_archived=False).with_totals()
    route, sender = Route(gym), get_sender()
    rows = []
    for member in members:
        if not member.phone or member.reminders_opted_out:
            counts["skipped"] += 1  # no number to send to, or they asked us to stop
            continue
        row = Message(gym=gym, member=member, kind=todo[member.id], dedupe_key=keys[member.id], to=member.phone,
                      for_date=for_date, provider=sender.name)
        route.fill_in(row, reminder_values(gym, member, row.kind, for_date))
        rows.append(row)
    if not rows or not queue(rows):
        return counts
    for row in rows:
        if row.status == Message.QUEUED:
            deliver(row, sender)
        counts["sent" if row.status == Message.SENT else "failed"] += 1
    return counts


# ---- Retries ----

def _claim(row: Message, now: datetime) -> bool:
    """Take a row waiting for its retry, so that no other run sends it too. Only one of two can change it."""
    claimed = Message.objects.filter(pk=row.pk, status=Message.QUEUED, attempts=row.attempts, next_retry_at=row.next_retry_at).update(
        attempts=F("attempts") + 1, next_retry_at=None, updated_at=now,
    )
    if claimed:
        row.attempts, row.next_retry_at = row.attempts + 1, None
    return bool(claimed)


def _give_up_on_interrupted(now: datetime) -> int:
    """Rows a crash left mid-send: counted as tried, so they may have gone. Say so, and don't send them again."""
    return Message.objects.filter(
        status=Message.QUEUED, next_retry_at=None, attempts__gte=1, updated_at__lt=now - INTERRUPTED_AFTER,
    ).update(status=Message.FAILED, error=INTERRUPTED, error_code="interrupted", updated_at=now)


def send_retries(now: datetime | None = None) -> dict[str, int]:
    """Try again every message whose wait after a temporary failure is over. Says how many went, failed for good,
    or are waiting again."""
    now = now or timezone.now()
    counts = {"sent": 0, "failed": 0, "waiting": 0, "interrupted": _give_up_on_interrupted(now)}
    due = (Message.objects.filter(status=Message.QUEUED, next_retry_at__lte=now)
           .select_related("gym__billing", "member", "template").order_by("next_retry_at")[:RETRY_BATCH])
    sender = get_sender()
    for row in due:
        if reason := stop_reason(row.gym, row.member):
            # Paused, switched off or opted out since it was queued: it doesn't go, and the row says why.
            if Message.objects.filter(pk=row.pk, status=Message.QUEUED, attempts=row.attempts).update(
                    status=Message.FAILED, error=reason, error_code="", next_retry_at=None, updated_at=now):
                counts["failed"] += 1
            continue
        if not _claim(row, now):
            continue  # another run took it
        deliver(row, sender, now)
        counts[{Message.SENT: "sent", Message.FAILED: "failed"}.get(row.status, "waiting")] += 1
    return counts
