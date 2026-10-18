"""Rackline invoices: each gym's invoice on its billing day, the charges added by hand, and the payments against them.

Everything that changes what a gym owes locks its `GymBilling` row first (then the invoice), so the invoice job, an
approval, a charge and a payment can't cross each other. Numbers come from `NumberSeries` under its own lock.
"""
from datetime import date, datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import OuterRef, Q
from django.utils import timezone

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.core.queries import sum_of
from apps.gyms.models import Gym
from apps.messages.automation import is_invoice_hour
from apps.messages.models import AutomationSchedule, WhatsAppTemplate
from apps.messages.notify import after_commit
from apps.messages.tasks import send_rackline_receipt
from apps.messages.usage import usage

from .models import PAY_WITHIN_DAYS, GymBilling, Invoice, InvoiceLine, InvoicePayment, NumberSeries, financial_year
from .services import branches_label, locked_plan

INVOICE, RECEIPT = ("invoice", "RL"), ("receipt", "RLR")  # (series, prefix): RL/2026-27/0001, RLR/2026-27/0001


def _span(starts: date, ends: date) -> str:
    return f"{clock.date_label(starts)} to {clock.date_label(ends)}"


def next_number(series: tuple[str, str], on: date) -> str:
    """The next number in a series for the financial year `on` falls in. Call it inside a transaction: the series
    row stays locked until it commits, so a number is never taken twice."""
    name, prefix = series
    year = financial_year(on)
    key = f"{name} {year}"
    try:
        with transaction.atomic():
            NumberSeries.objects.get_or_create(name=key)
    except IntegrityError:  # another writer started the year's series a moment ago
        pass
    row = NumberSeries.objects.select_for_update().get(name=key)
    row.last += 1
    row.save(update_fields=["last"])
    return f"{prefix}/{year}/{row.last:04d}"


def owed_by_gym():
    """What each gym owes Rackline (its open invoices less what's paid on them), as an annotation on gyms."""
    billed = sum_of(Invoice.objects.filter(gym=OuterRef("pk"), status=Invoice.OPEN), "total_paise")
    paid = sum_of(InvoicePayment.objects.filter(gym=OuterRef("pk"), invoice__status=Invoice.OPEN, voided=False), "amount_paise")
    return billed - paid


def owed(gym: Gym) -> int:
    return Gym.objects.filter(pk=gym.pk).annotate(owed=owed_by_gym()).values_list("owed", flat=True).first() or 0


def _paid_until(plan: GymBilling) -> None:
    """The last day the gym's paid invoices cover. Follows every payment, void and voided payment."""
    plan.paid_until = (Invoice.objects.filter(gym_id=plan.gym_id, status=Invoice.PAID)
                       .order_by("-period_to").values_list("period_to", flat=True).first())
    plan.save(update_fields=["paid_until", "updated_at"])


# Writing invoices

def whatsapp_usage_lines(plan: GymBilling, starts: date) -> list[InvoiceLine]:
    """The billing month before `starts`: delivered messages on Rackline's shared number, one line for each Meta
    category and rate kept on the messages (a rate that changed mid-month shows as two lines)."""
    first, last = clock.add_months(starts, -1), starts - timedelta(days=1)
    category = dict(WhatsAppTemplate.CATEGORIES)
    return [
        InvoiceLine(gym=plan.gym, kind=InvoiceLine.WHATSAPP_USAGE, starts=first, ends=last, quantity=row["messages"],
                    rate_paise=row["rate_paise"], amount_paise=row["amount_paise"],
                    description=f"WhatsApp messages delivered ({category.get(row['category'], 'other').lower()}), {_span(first, last)}")
        for row in usage(plan.gym, first, last)
    ]


@transaction.atomic
def write_invoice(gym: Gym, starts: date) -> Invoice | None:
    """The gym's invoice for the billing month from `starts`: the base fee and branches for the month ahead, the
    branches added the month before, pending charges and last month's WhatsApp messages. None when that month
    already has an invoice (void or not), so running it again writes nothing."""
    plan = locked_plan(gym)
    if Invoice.objects.filter(gym=gym, period_from=starts).exists():
        return None
    ends = clock.add_months(starts, 1) - timedelta(days=1)
    pending = list(InvoiceLine.objects.filter(gym=gym, invoice=None).filter(Q(starts=None) | Q(starts__lte=ends)))
    # A request approved on or after `starts` is already in the quota, and its own line charges it from the day it
    # was approved: the month's branch line leaves it out, so it's billed once.
    added = sum(p.quantity for p in pending if p.kind == InvoiceLine.BRANCHES_PRO_RATA and p.starts >= starts)
    branches = max(plan.branch_quota - added, 0)
    month = {"gym": gym, "starts": starts, "ends": ends}
    lines = [InvoiceLine(kind=InvoiceLine.BASE, description=f"Rackline plan, {_span(starts, ends)}", rate_paise=plan.base_paise,
                         amount_paise=plan.base_paise, **month)]
    if branches:
        lines.append(InvoiceLine(kind=InvoiceLine.BRANCHES, description=f"{branches_label(branches)}, {_span(starts, ends)}",
                                 quantity=branches, rate_paise=plan.per_branch_paise, amount_paise=plan.per_branch_paise * branches, **month))
    lines += whatsapp_usage_lines(plan, starts)
    subtotal = sum(line.amount_paise for line in lines + pending)
    tax = sum(line.tax_paise for line in lines + pending)
    inv = Invoice.objects.create(
        gym=gym, number=next_number(INVOICE, starts), period_from=starts, period_to=ends, issued_on=starts,
        due_on=starts + timedelta(days=PAY_WITHIN_DAYS), subtotal_paise=subtotal, tax_paise=tax, total_paise=subtotal + tax,
        status=Invoice.OPEN if subtotal + tax else Invoice.PAID,  # nothing to pay (a plan at ₹0) is paid as it's written
    )
    for line in lines:
        line.invoice = inv
    InvoiceLine.objects.bulk_create(lines)
    InvoiceLine.objects.filter(pk__in=[p.pk for p in pending]).update(invoice=inv, updated_at=timezone.now())
    if inv.status == Invoice.PAID:
        _paid_until(plan)
    return inv


def gyms_billed_on(day: date | None = None, now: datetime | None = None):
    """(gym, day) for every active gym whose billing day is today on its own clock and whose clock has reached
    Rackline's invoice hour (AutomationSchedule), or every gym billed on `day` when given (a day the worker
    missed, any hour). Trial and suspended gyms aren't billed."""
    schedule = AutomationSchedule.current()
    for plan in GymBilling.objects.filter(gym__status=Gym.ACTIVE).select_related("gym").iterator():
        if day is None and not is_invoice_hour(plan.gym, now, schedule):
            continue
        on = day or clock.local(plan.gym, now).date()
        if on.day == plan.billing_day:
            yield plan.gym, on


# Charges added by hand

CHARGE_TEXT = {InvoiceLine.WHATSAPP_SETUP: "WhatsApp setup", InvoiceLine.MACHINE_SETUP: "Attendance machine setup"}


@transaction.atomic
def add_charge(gym: Gym, *, kind: str, quantity: int = 1, rate_paise: int | None = None, description: str = "", by) -> InvoiceLine:
    """Add Charge: a pending line for the gym's next invoice. Setup fees default to the gym's own prices."""
    plan = locked_plan(gym)
    if kind not in InvoiceLine.CHARGES:
        raise RuleBroken("not_a_charge", "Add a WhatsApp setup, a machine setup or another charge")
    if rate_paise is None:
        if kind == InvoiceLine.ADJUSTMENT:
            raise RuleBroken("rate_needed", "Enter what the charge is")
        rate_paise = plan.whatsapp_setup_paise if kind == InvoiceLine.WHATSAPP_SETUP else plan.machine_setup_paise
    text = description.strip() or CHARGE_TEXT.get(kind, "")
    if not text:
        raise RuleBroken("description_needed", "Say what the charge is for")
    if kind == InvoiceLine.MACHINE_SETUP and quantity > 1 and not description.strip():
        text = f"{text}, {quantity} machines"
    return InvoiceLine.objects.create(gym=gym, kind=kind, description=text[:200], quantity=quantity, rate_paise=rate_paise,
                                      amount_paise=rate_paise * quantity, added_by=by)


@transaction.atomic
def remove_charge(line: InvoiceLine) -> None:
    """Take back a charge added by hand before an invoice bills it. Billed lines and pro-rata branches stay."""
    locked_plan(line.gym)
    line = InvoiceLine.objects.select_for_update().get(pk=line.pk)
    if line.invoice_id is not None:
        raise RuleBroken("billed", "This charge is on an invoice now. Void the invoice to cancel it.")
    if line.kind not in InvoiceLine.CHARGES:
        raise RuleBroken("not_a_charge", "Branches added during the month are billed as approved")
    line.delete()  # never billed and never paid: nothing to keep but the audit row the view writes


# Payments and voids

def _locked_invoice(inv: Invoice) -> tuple[GymBilling, Invoice]:
    plan = locked_plan(inv.gym)
    return plan, Invoice.objects.select_for_update().get(pk=inv.pk)


@transaction.atomic
def record_payment(inv: Invoice, *, amount_paise: int, method: str, paid_on: date, reference: str = "", by) -> InvoicePayment:
    """Record Payment: all or part of what the invoice owes, never more. Paid in full, it moves `paid_until`."""
    plan, inv = _locked_invoice(inv)
    if inv.status == Invoice.VOID:
        raise RuleBroken("invoice_void", f"{inv.number} is void. Nothing can be paid on it.")
    if paid_on > timezone.localdate():
        raise RuleBroken("future_date", "Pick the day the money came in: today or before")
    owes = inv.owed_paise()
    if owes <= 0:
        raise RuleBroken("nothing_owed", f"{inv.number} is paid in full")
    if amount_paise > owes:
        raise RuleBroken("overpaid", f"{inv.number} owes {rupees(owes)}. Record that or less.")
    pay = InvoicePayment.objects.create(gym=inv.gym, invoice=inv, receipt_number=next_number(RECEIPT, paid_on), amount_paise=amount_paise,
                                        method=method, reference=reference.strip(), paid_on=paid_on, recorded_by=by)
    if amount_paise == owes:
        inv.status = Invoice.PAID
        inv.save(update_fields=["status", "updated_at"])
        _paid_until(plan)
    after_commit(send_rackline_receipt, pay.pk)  # the owner hears it arrived
    return pay


@transaction.atomic
def void_payment(pay: InvoicePayment, *, reason: str, by) -> InvoicePayment:
    """A payment that never came in: it stays on the invoice, voided, and what it paid is owed again."""
    plan, inv = _locked_invoice(pay.invoice)
    pay = InvoicePayment.objects.select_for_update().get(pk=pay.pk)
    if pay.voided:
        raise RuleBroken("already_void", f"Receipt {pay.receipt_number} is already void")
    pay.voided, pay.void_reason, pay.voided_by, pay.voided_at = True, reason.strip(), by, timezone.now()
    pay.save()
    if inv.status == Invoice.PAID:
        inv.status = Invoice.OPEN
        inv.save(update_fields=["status", "updated_at"])
        _paid_until(plan)
    return pay


@transaction.atomic
def void_invoice(inv: Invoice, *, reason: str, by) -> Invoice:
    """An invoice that should never have been written. It keeps its number and lines; nothing on it is billed again
    by itself (Add Charge bills what should be). Payments on it are voided first."""
    plan, inv = _locked_invoice(inv)
    if inv.status == Invoice.VOID:
        raise RuleBroken("already_void", f"{inv.number} is already void")
    if inv.payments.filter(voided=False).exists():
        raise RuleBroken("has_payments", "Void its payments first, so what was paid is clear")
    was_paid = inv.status == Invoice.PAID
    inv.status, inv.void_reason, inv.voided_by, inv.voided_at = Invoice.VOID, reason.strip(), by, timezone.now()
    inv.save()
    if was_paid:
        _paid_until(plan)
    return inv
