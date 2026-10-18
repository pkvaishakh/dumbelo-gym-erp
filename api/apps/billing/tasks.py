"""The scheduled side of Rackline billing: writing each gym's invoice on its billing day. The rules live in invoicing.py."""
import logging
from datetime import date, datetime

from celery import shared_task

from apps.audit.models import record
from apps.core.jobs import run_job
from apps.core.models import JobRun

from . import invoicing

log = logging.getLogger(__name__)


def invoice_tick(day: date | None = None, now: datetime | None = None) -> dict[str, int]:
    """Write the invoice of every active gym whose billing day it is, on its own clock from Rackline's invoice hour
    (or `day`). Safe to repeat: a month with an invoice is skipped. One gym's failure is logged and never stops
    the rest. Says how many were written and how many gyms' failed."""
    counts = {"written": 0, "failed": 0}
    for gym, on in invoicing.gyms_billed_on(day, now):
        try:
            inv = invoicing.write_invoice(gym, on)
        except Exception:
            log.exception("Couldn't write the Rackline invoice of gym %s for %s", gym.pk, on)
            counts["failed"] += 1
            continue
        if inv is not None:
            record(None, "invoice.written", inv, None, {"number": inv.number, "total_paise": inv.total_paise}, gym=gym)
            counts["written"] += 1
    return counts


def write_due(day: date | None = None, now: datetime | None = None) -> int:
    """`invoice_tick` without keeping a run: how many invoices it wrote."""
    return invoice_tick(day, now)["written"]


@shared_task
def write_invoices(day: str | None = None, run_id: int | None = None, by_hand: bool = False):
    """The job beat runs every hour (`CELERY_BEAT_SCHEDULE`): each gym's billing day starts at its own midnight, the
    invoice is written from Rackline's invoice hour (read on every tick), and the ticks after that find it written.
    `day` (YYYY-MM-DD) writes a billing day the worker missed; Run Now passes the run it queued; `by_hand` is
    `manage.py write_invoices`. Every run is kept (`apps.core.jobs`). Returns how many invoices were written, for
    the worker's log."""
    on = date.fromisoformat(day) if day else None
    counts = run_job(JobRun.INVOICES, lambda: invoice_tick(on), run_id=run_id, by_hand=by_hand or day is not None)
    return counts.get("written", 0)
