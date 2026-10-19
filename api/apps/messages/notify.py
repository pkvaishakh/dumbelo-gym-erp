"""Messages about something that just happened, rather than the daily reminders: a member's receipt, a task
given to a staff member, and Dumbelo's own messages to a gym's owner (an invoice coming due or late, a payment
received).

Each goes once, under a key unique in its gym: `payment:<id>`, `task:<id>:to:<staff role id>` (handing the task
to someone else tells them too), `invoice:<id>:due:<day>`, `dumbelo-receipt:<id>`. A receipt or a task message is
queued only once the transaction that saved the payment or task commits (`after_commit`), so a payment that rolled
back never sends one. Each checks its switch (`automation.py`) when it sends.
"""
import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Invoice, InvoicePayment
from apps.core import clock
from apps.core.money import rupees
from apps.gyms.models import Gym, GymRole
from apps.members.models import Payment
from apps.tasks.models import Task

from . import automation
from .models import AutomationSchedule, Message, NotificationRule
from .services import Route, plan_label, send_one, stop_reason

log = logging.getLogger(__name__)

#: When a gym's owner hears about an open Dumbelo invoice, in days until it's due: 3 days before, then the day
#: after it was due and a week after that, while something is still owed.
INVOICE_DUE_DAYS = (3, -1, -7)


def after_commit(task, *args) -> None:
    """Queue a Celery task once the transaction in progress commits (at once outside one). A failure to queue it is
    logged, never the caller's: the payment or task it is about is already saved."""
    def go():
        try:
            task.delay(*args)
        except Exception:
            log.exception("Couldn't queue %s for %r", task.name, args)
    transaction.on_commit(go)


def first_name(name: str) -> str:
    return name.split()[0] if name.split() else name


def owner_of(gym: Gym) -> GymRole | None:
    """The gym's account owner, who hears from Dumbelo about its invoices. None when it has no active one."""
    return GymRole.objects.filter(gym=gym, is_owner=True, is_active=True).select_related("user").first()


# ---- The gym's own messages ----

def payment_received(payment_id: int) -> Message | None:
    """The member's receipt for a payment just recorded. Off until the gym turns it on; never for a voided one."""
    pay = Payment.objects.select_related("gym__billing", "member", "subscription__plan").filter(pk=payment_id).first()
    if pay is None or pay.voided:
        return None
    gym, member = pay.gym, pay.member
    if not automation.is_on(gym, NotificationRule.PAYMENT_RECEIVED) or stop_reason(gym, member) or not member.phone:
        return None
    paid_on = clock.local(gym, pay.taken_at).date()
    row = Message(gym=gym, member=member, kind=NotificationRule.PAYMENT_RECEIVED, dedupe_key=f"payment:{pay.pk}",
                  to=member.phone, for_date=paid_on)
    values = {"first_name": first_name(member.name), "amount": rupees(pay.amount_paise), "plan": plan_label(pay.subscription),
              "gym": gym.name, "paid_on": clock.date_label(paid_on)}
    return send_one(gym, row, values, Route(gym))


def _due(task: Task) -> str:
    day = clock.date_label(task.due_date)
    return f"{day} by {clock.clock_label(task.due_time)}" if task.due_time else day


def task_assigned(task_id: int) -> Message | None:
    """Tell a trainer or receptionist about the task an admin just gave them. Nothing once it's done, or to staff
    who have left or have no number."""
    task = Task.objects.select_related("gym__billing", "assignee__user").filter(pk=task_id).first()
    if task is None or task.status == Task.DONE or not task.assignee.is_active:
        return None
    gym, user = task.gym, task.assignee.user
    if not automation.is_on(gym, NotificationRule.TASK_ASSIGNED) or stop_reason(gym) or not user.phone:
        return None
    row = Message(gym=gym, user=user, kind=NotificationRule.TASK_ASSIGNED, dedupe_key=f"task:{task.pk}:to:{task.assignee_id}",
                  to=user.phone, for_date=clock.today(gym))
    values = {"first_name": first_name(user.name), "task": task.title, "gym": gym.name, "due_date": _due(task)}
    return send_one(gym, row, values, Route(gym))


# ---- Dumbelo's messages to the owner ----
# From Dumbelo's shared number whatever the gym's WhatsApp mode, and never billed to the gym. A suspended gym's
# owner still hears about its invoices: paying them is how it opens again.

def dumbelo_payment_received(payment_id: int) -> Message | None:
    """Tell the owner Dumbelo received their payment, with the receipt's number."""
    pay = InvoicePayment.objects.select_related("gym").filter(pk=payment_id).first()
    if pay is None or pay.voided:
        return None
    gym = pay.gym
    owner = owner_of(gym)
    if not automation.is_on(gym, NotificationRule.DUMBELO_PAYMENT_RECEIVED) or owner is None or not owner.user.phone:
        return None
    row = Message(gym=gym, user=owner.user, kind=NotificationRule.DUMBELO_PAYMENT_RECEIVED, dedupe_key=f"dumbelo-receipt:{pay.pk}",
                  to=owner.user.phone, for_date=clock.today(gym))
    values = {"first_name": first_name(owner.user.name), "gym": gym.name, "amount": rupees(pay.amount_paise),
              "receipt_number": pay.receipt_number}
    return send_one(gym, row, values, Route(gym, dumbelo=True))


def invoice_reminders(now: datetime | None = None) -> int:
    """Remind owners about open Dumbelo invoices on INVOICE_DUE_DAYS, at the hour of the gym's invoice reminder
    on its own clock. Safe to repeat: one message an invoice a day. Returns how many went."""
    now = now or timezone.now()
    today = timezone.localdate(now)  # Dumbelo's day: every gym's own is within a day of it
    window = (today + timedelta(days=min(INVOICE_DUE_DAYS) - 1), today + timedelta(days=max(INVOICE_DUE_DAYS) + 1))
    invoices = list(Invoice.objects.filter(status=Invoice.OPEN, due_on__range=window).with_paid().select_related("gym"))
    if not invoices:
        return 0
    gyms = list({inv.gym_id: inv.gym for inv in invoices}.values())
    rules = automation.rules_by_gym(gyms, AutomationSchedule.current())
    owners = {r.gym_id: r for r in GymRole.objects.filter(gym__in=gyms, is_owner=True, is_active=True).select_related("user")}
    route, sent = None, 0
    for inv in invoices:
        gym, owner = inv.gym, owners.get(inv.gym_id)
        rule, here = rules[gym.pk][NotificationRule.DUMBELO_INVOICE_DUE], clock.local(gym, now)
        if not rule.is_on or rule.hour != here.hour or (inv.due_on - here.date()).days not in INVOICE_DUE_DAYS:
            continue
        if owner is None or not owner.user.phone or inv.owed_paise() <= 0:
            continue
        route = route or Route(gym, dumbelo=True)  # the shared number and its templates, the same for every gym
        row = Message(gym=gym, user=owner.user, kind=NotificationRule.DUMBELO_INVOICE_DUE, to=owner.user.phone,
                      dedupe_key=f"invoice:{inv.pk}:due:{here.date().isoformat()}", for_date=here.date())
        values = {"first_name": first_name(owner.user.name), "gym": gym.name, "invoice_number": inv.number,
                  "amount": rupees(inv.owed_paise()), "due_date": clock.date_label(inv.due_on)}
        message = send_one(gym, row, values, route)
        sent += bool(message and message.status == Message.SENT)
    return sent
