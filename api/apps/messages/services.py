"""Turning today's reminder list into messages, and the words the member reads.

`apps.reminders` works out who has earned a nudge; this sends it. The rules are the gym's: one message a
member a day, nothing to someone who asked us to stop, and nothing at all while the gym has reminders off.
"""
from datetime import date

from apps.core import clock
from apps.core.money import rupees
from apps.members.models import Member
from apps.reminders.models import ReminderDue

from .models import Message
from .senders import get_sender

#: Which reminder a member hears about when they have earned more than one: the plan that runs out today
#: first, then money owed, then the earlier warnings. Everything else can wait for tomorrow's message.
PRIORITY = [ReminderDue.EXPIRING_0, ReminderDue.DUES, ReminderDue.EXPIRING_3, ReminderDue.EXPIRING_7]


def plan_label(sub) -> str:
    """'Monthly plan' — the plan's name with the word plan, unless the gym already named it that."""
    if sub is None:
        return "membership"
    name = sub.plan.name.strip()
    return name if name.lower().endswith(("plan", "membership", "pack")) else f"{name} plan"


def text_for(gym, member: Member, kind: str, for_date: date) -> str:
    """What one reminder says. Plain words, their first name, and what to do about it."""
    first = member.name.split()[0] if member.name.split() else member.name
    sub = member.current_subscription(for_date)
    plan = plan_label(sub)
    if kind == ReminderDue.DUES:
        return (
            f"Hi {first}, {rupees(member.balance_paise())} is still to pay on your {plan} at {gym.name}. "
            f"You can pay it at the front desk the next time you come in."
        )
    if sub is None or sub.ends <= for_date:
        return f"Hi {first}, your {plan} at {gym.name} ends today. Renew it at the front desk to keep checking in."
    days = (sub.ends - for_date).days
    when = "tomorrow" if days == 1 else f"in {days} days"
    return (
        f"Hi {first}, your {plan} at {gym.name} ends on {clock.date_label(sub.ends)}, {when}. "
        f"Renew it at the front desk to keep checking in."
    )


def _one_kind_per_member(gym, for_date: date) -> dict[int, str]:
    """The single reminder each member is owed today, by member id (see PRIORITY)."""
    rank = {kind: i for i, kind in enumerate(PRIORITY)}
    best: dict[int, str] = {}
    for member_id, kind in ReminderDue.objects.filter(gym=gym, for_date=for_date).values_list("member_id", "kind"):
        if member_id not in best or rank.get(kind, len(rank)) < rank.get(best[member_id], len(rank)):
            best[member_id] = kind
    return best


def send_due(gym, for_date: date) -> dict[str, int]:
    """Send the gym's reminders for one local day. Says how many went and how many didn't.

    Safe to run again: the day's messages are already on record, so a second run sends nothing.
    """
    counts = {"sent": 0, "failed": 0, "skipped": 0}
    if not gym.reminders_on:
        return counts
    wanted = _one_kind_per_member(gym, for_date)
    if not wanted:
        return counts
    already = set(Message.objects.filter(gym=gym, for_date=for_date).values_list("member_id", flat=True))
    todo = {member_id: kind for member_id, kind in wanted.items() if member_id not in already}
    if not todo:
        return counts
    # with_totals() brings the balance and the current plan the words need, for every member in two queries
    members = Member.objects.filter(gym=gym, id__in=todo, is_archived=False).with_totals()
    sender = get_sender()
    for member in members:
        if not member.phone or member.reminders_opted_out:
            counts["skipped"] += 1  # no number to send to, or they asked us to stop
            continue
        text = text_for(gym, member, todo[member.id], for_date)
        row = Message(gym=gym, member=member, kind=todo[member.id], to=member.phone, text=text, for_date=for_date, provider=sender.name)
        try:
            row.provider_id, row.status = sender.send(member.phone, text), Message.SENT
        except Exception as e:
            # One member's failure is never the gym's: a provider that is down, or a number it won't take,
            # is written down and the rest of the morning's messages still go out. Anything the provider's
            # own client raises counts, not only SendFailed.
            row.status, row.error = Message.FAILED, str(e)[:200] or e.__class__.__name__
        # Saved one at a time, not in bulk: a message that has gone out must be on record even if the job dies.
        row.save()
        counts["sent" if row.status == Message.SENT else "failed"] += 1
    return counts
