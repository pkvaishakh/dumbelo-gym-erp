"""The record every scheduled job keeps of its runs (`JobRun`), for the Console's Server screen.

A job's work runs inside `run_job`, which writes the run as it starts and finishes it with what the work counted, or
with the error if it broke. Each finish prunes its own job: runs that did nothing are kept only as the latest, the
rest for KEEP. Run Now queues a run (`queue`) that the worker then takes by its id; a run left unfinished past
STALE_AFTER (the worker restarted mid-run, or the queue lost it) is closed as abandoned, so it can't block Run Now.
"""
import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import JobRun

log = logging.getLogger(__name__)

KEEP = timedelta(days=30)
STALE_AFTER = timedelta(hours=1)
ABANDONED = "It stopped without finishing: the worker may have restarted"


def close_abandoned(job: str, now: datetime) -> int:
    """Finish the job's runs that were queued or started more than STALE_AFTER ago and never finished."""
    old = JobRun.objects.annotate(began=Coalesce("started_at", "created_at")).filter(
        job=job, finished_at__isnull=True, began__lt=now - STALE_AFTER)
    return old.update(finished_at=now, error=ABANDONED)


def running(job: str) -> JobRun | None:
    """The job's run that is queued or under way, if any."""
    return JobRun.objects.filter(job=job, finished_at__isnull=True).first()


def _start(job: str, run_id: int | None, trigger: str, now: datetime) -> JobRun | None:
    if run_id is None:
        close_abandoned(job, now)
        return JobRun.objects.create(job=job, trigger=trigger, started_at=now)
    # Run Now's row: taken once, so a task the queue hands over twice runs once
    if not JobRun.objects.filter(pk=run_id, job=job, started_at__isnull=True, finished_at__isnull=True).update(started_at=now):
        return None
    return JobRun.objects.get(pk=run_id)


def _finish(run: JobRun, counts: dict[str, int], error: str = "") -> None:
    now = timezone.now()
    run.finished_at, run.counts, run.error = now, counts, error
    run.idle = not error and not any(counts.values())
    run.save(update_fields=["finished_at", "counts", "error", "idle"])
    done = JobRun.objects.filter(job=run.job, finished_at__isnull=False).exclude(pk=run.pk)
    done.filter(Q(idle=True) | Q(created_at__lt=now - KEEP)).delete()


def _why(e: Exception) -> str:
    """The error's kind and first line only: a database error's details can quote rows."""
    first = (str(e).strip().splitlines() or [""])[0]
    return (f"{e.__class__.__name__}: {first}" if first else e.__class__.__name__)[:200]


def run_job(job: str, work: Callable[[], dict[str, int]], *, run_id: int | None = None, by_hand: bool = False) -> dict[str, int]:
    """Run `work` as one run of `job` and keep the record. `run_id` is a run Run Now queued; without it the run is
    beat's, or by hand when someone asked for a particular day or time. Says what the work counted ({} when Run Now's
    run was already taken). An error is kept on the run and raised again, so the worker's log has it too."""
    trigger = JobRun.RUN_NOW if run_id is not None else JobRun.BY_HAND if by_hand else JobRun.BEAT
    run = _start(job, run_id, trigger, timezone.now())
    if run is None:
        log.info("Run %s of %s was already taken or closed; nothing to do", run_id, job)
        return {}
    try:
        counts = work()
    except Exception as e:
        _finish(run, {}, _why(e))
        raise
    _finish(run, counts)
    return counts


def queue(job: str, by) -> JobRun:
    """Write Run Now's run, waiting for the worker. Raises IntegrityError when one is already waiting or under way."""
    close_abandoned(job, timezone.now())
    with transaction.atomic():  # a savepoint, so a refused insert leaves the caller's transaction usable
        return JobRun.objects.create(job=job, trigger=JobRun.RUN_NOW, by=by)
