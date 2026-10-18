"""When messages go out and whether they go at all: Rackline's schedule, each gym's switches, and the times a
Rackline admin set for one gym.

The times are Rackline's (`AutomationSchedule`): a gym's admins pause and resume their gym's messages, never
change when they go. Every job reads these on every tick, so a change applies on the next one.
"""
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime

from django.db import transaction

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.gyms.models import Gym

from .models import AutomationSchedule, NotificationRule, WhatsAppTemplate

MAX_DAYS_AHEAD = 60  # warning further ahead than two months is noise, not a reminder
MAX_WARNINGS = 3


@dataclass(frozen=True)
class Rule:
    """One message for one gym, as it stands: on or paused, and when it goes (for the ones sent at an hour)."""

    kind: str
    is_on: bool
    hour: int | None = None  # in the gym's time zone; None for messages sent when something happens
    days_ahead: tuple[int, ...] | None = None  # a plan ending soon only
    gyms_own_time: bool = False  # a Rackline admin set this gym's hour or days in place of Rackline's

    @property
    def label(self) -> str:
        return dict(WhatsAppTemplate.KINDS)[self.kind]


def clean_days(days: Iterable[int]) -> list[int]:
    """Days ahead as they are kept: whole days, each once, furthest first."""
    days = sorted({int(d) for d in days}, reverse=True)
    if not days or len(days) > MAX_WARNINGS:
        raise RuleBroken("days_ahead", f"Pick 1 to {MAX_WARNINGS} days")
    if days[-1] < 1 or days[0] > MAX_DAYS_AHEAD:
        raise RuleBroken("days_ahead", f"Pick days from 1 to {MAX_DAYS_AHEAD} before the plan ends")
    return days


def _rule(kind: str, row: NotificationRule | None, schedule: AutomationSchedule) -> Rule:
    is_on = row.is_on if row else kind not in NotificationRule.OFF_BY_DEFAULT
    if kind not in NotificationRule.SCHEDULED:
        return Rule(kind, is_on)
    hour = row.hour if row and row.hour is not None else schedule.reminder_hour
    days = None
    if kind == NotificationRule.PLAN_ENDING:
        days = tuple(row.days_ahead if row and row.days_ahead else schedule.days_ahead)
    own = bool(row and (row.hour is not None or row.days_ahead))
    return Rule(kind, is_on, hour, days, own)


def rules_for(gym: Gym, schedule: AutomationSchedule | None = None, rows: Iterable[NotificationRule] | None = None) -> dict[str, Rule]:
    """Every message's rule for the gym, by kind. `rows` are the gym's NotificationRule rows when a caller has them."""
    schedule = schedule or AutomationSchedule.current()
    by_kind = {r.kind: r for r in (NotificationRule.objects.filter(gym=gym) if rows is None else rows)}
    return {kind: _rule(kind, by_kind.get(kind), schedule) for kind, _ in WhatsAppTemplate.KINDS}


def is_on(gym: Gym, kind: str) -> bool:
    """Whether the gym's message of this kind may go out: its switch alone, not the gym's account or WhatsApp mode."""
    row = NotificationRule.objects.filter(gym=gym, kind=kind).only("is_on").first()
    return row.is_on if row else kind not in NotificationRule.OFF_BY_DEFAULT


def rules_by_gym(gyms: list[Gym], schedule: AutomationSchedule) -> dict[int, dict[str, Rule]]:
    """rules_for for many gyms in one query."""
    rows: dict[int, list[NotificationRule]] = {g.pk: [] for g in gyms}
    for row in NotificationRule.objects.filter(gym__in=gyms):
        rows[row.gym_id].append(row)
    return {g.pk: rules_for(g, schedule, rows[g.pk]) for g in gyms}


# ---- Which gyms' reminders are due on this tick ----

@dataclass(frozen=True)
class ReminderRun:
    """A gym whose clock has reached the hour of one or more of its reminders: the day's list is written, and
    the reminders whose hour it is (and are switched on) are sent."""

    gym: Gym
    day: date  # the gym's local date
    days_ahead: tuple[int, ...]
    send: frozenset[str]  # the reminder kinds that go out now


def reminder_runs(now: datetime | None = None) -> Iterator[ReminderRun]:
    """The open gyms whose own clock is in the hour of one of their reminders. Paused reminders still write the
    list, so the desk sees who to chase; they just aren't in `send`."""
    schedule = AutomationSchedule.current()
    gyms = list(Gym.objects.filter(status__in=Gym.OPEN).select_related("billing"))
    rules = rules_by_gym(gyms, schedule)
    for gym in gyms:
        here = clock.local(gym, now)
        mine = {k: rules[gym.pk][k] for k in NotificationRule.REMINDERS}
        due = [r for r in mine.values() if r.hour == here.hour]
        if due:
            send = frozenset(r.kind for r in due if r.is_on)
            yield ReminderRun(gym, here.date(), mine[NotificationRule.PLAN_ENDING].days_ahead or (), send)


def is_invoice_hour(gym: Gym, now: datetime | None = None, schedule: AutomationSchedule | None = None) -> bool:
    """Whether the gym's clock has reached the hour Rackline's invoices are written. Later ticks the same day are
    in time too (the job skips a month already written), so a missed tick doesn't lose the day."""
    return clock.local(gym, now).hour >= (schedule or AutomationSchedule.current()).invoice_hour


# ---- Changes ----

SCHEDULE_FIELDS = ("reminder_hour", "days_ahead", "invoice_hour")


def audit_schedule(schedule: AutomationSchedule) -> dict:
    return {f: getattr(schedule, f) for f in SCHEDULE_FIELDS}


@transaction.atomic
def change_schedule(*, by, **fields) -> AutomationSchedule:
    """Rackline's times for every gym. Applies on each job's next tick."""
    schedule = AutomationSchedule.objects.select_for_update().filter(pk=1).first() or AutomationSchedule(pk=1)
    if "days_ahead" in fields:
        fields["days_ahead"] = clean_days(fields["days_ahead"])
    for field, value in fields.items():
        if field in SCHEDULE_FIELDS:
            setattr(schedule, field, value)
    schedule.updated_by = by
    schedule.save()
    return schedule


def audit_rule(rule: Rule) -> dict:
    return {"is_on": rule.is_on, "hour": rule.hour, "days_ahead": list(rule.days_ahead) if rule.days_ahead else None}


def _row(gym: Gym, kind: str) -> NotificationRule:
    if kind not in dict(WhatsAppTemplate.KINDS):
        raise RuleBroken("not_a_message", "There's no such message")
    row = NotificationRule.objects.select_for_update().filter(gym=gym, kind=kind).first()
    return row or NotificationRule(gym=gym, kind=kind, is_on=kind not in NotificationRule.OFF_BY_DEFAULT)


@transaction.atomic
def switch(gym: Gym, kind: str, on: bool, *, rackline: bool) -> NotificationRule:
    """Pause or Resume one message. A gym's admins switch the gym's own messages; Rackline admins (`rackline`) the
    ones Rackline sends the owner."""
    allowed = NotificationRule.RACKLINE_KINDS if rackline else NotificationRule.GYM_KINDS
    if kind not in allowed:
        raise RuleBroken("not_yours", "Rackline switches its own messages to you" if not rackline
                         else "The gym's admins pause and resume the gym's own messages")
    row = _row(gym, kind)
    row.is_on = on
    row.save()
    return row


@transaction.atomic
def set_times(gym: Gym, kind: str, **times) -> NotificationRule:
    """A Rackline admin's `hour` and `days_ahead` for one of the gym's messages, in place of Rackline's; one left
    out stays as it was. None is Rackline's again (both None: Use Rackline's Times)."""
    if kind not in NotificationRule.SCHEDULED:
        raise RuleBroken("not_scheduled", "This message goes out when it happens, not at a set time")
    if times.get("days_ahead") is not None and kind != NotificationRule.PLAN_ENDING:
        raise RuleBroken("no_days", "Only the plan ending message goes out days ahead")
    row = _row(gym, kind)
    if "hour" in times:
        row.hour = times["hour"]
    if "days_ahead" in times:
        row.days_ahead = clean_days(times["days_ahead"]) if times["days_ahead"] else None
    row.save()
    return row
