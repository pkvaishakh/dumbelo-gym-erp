"""The scheduled side of Rackline billing: writing each gym's invoice on its billing day. The rules live in invoicing.py."""
import logging
from datetime import date

from celery import shared_task

from apps.audit.models import record

from . import invoicing

log = logging.getLogger(__name__)


def write_due(day: date | None = None) -> int:
    """Write the invoice of every active gym whose billing day it is, on its own clock (or `day`). Safe to repeat:
    a month with an invoice is skipped. One gym's failure is logged and never stops the rest."""
    written = 0
    for gym, on in invoicing.gyms_billed_on(day):
        try:
            inv = invoicing.write_invoice(gym, on)
        except Exception:
            log.exception("Couldn't write the Rackline invoice of gym %s for %s", gym.pk, on)
            continue
        if inv is not None:
            record(None, "invoice.written", inv, None, {"number": inv.number, "total_paise": inv.total_paise}, gym=gym)
            written += 1
    return written


@shared_task
def write_invoices(day: str | None = None):
    """The job beat runs every hour (`CELERY_BEAT_SCHEDULE`): each gym's day turns at its own midnight, and the ticks
    after the first find the invoice written. `day` (YYYY-MM-DD) writes a billing day the worker missed. Returns how
    many invoices were written, for the worker's log."""
    return write_due(date.fromisoformat(day) if day else None)
