"""Run Meta's webhook calls again from what was kept: `python manage.py replay_webhook_events`.

    python manage.py replay_webhook_events --since 2026-10-18T09:00+05:30   # every call since then, India time
    python manage.py replay_webhook_events --since 2026-10-18 --failed      # only the ones that couldn't be handled
    python manage.py replay_webhook_events --id 812 --id 813

For a status that came before its send saved Meta's id, or a call that broke on a bug since fixed. Safe to run
again: statuses only move forward and a reply is acted on once.
"""
from datetime import UTC, datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core.jobs import run_job
from apps.core.models import JobRun
from apps.messages.models import WebhookEvent
from apps.messages.webhook import replay


def _since(value: str) -> datetime:
    """An ISO time, or a day (from its start). Without a time zone it is UTC, as everything stored is."""
    try:
        at = datetime.fromisoformat(value)  # a bare day is its midnight
    except ValueError:
        raise CommandError("Give --since as YYYY-MM-DD or YYYY-MM-DDTHH:MM") from None
    return at if timezone.is_aware(at) else at.replace(tzinfo=UTC)


class Command(BaseCommand):
    help = "Handle kept WhatsApp webhook calls again, oldest first: the ones since a time, the ones that failed, or by id."

    def add_arguments(self, parser):
        parser.add_argument("--since", default="", help="Calls kept from this time on (UTC unless it says otherwise)")
        parser.add_argument("--id", type=int, action="append", default=[], dest="ids", help="One call's id; give it again for more")
        parser.add_argument("--failed", action="store_true", help="Only calls that couldn't be handled")

    def handle(self, *args, since="", ids=(), failed=False, **kw):
        if not since and not ids:
            raise CommandError("Say which calls: --since a time, or --id.")
        events = WebhookEvent.objects.all()
        if since:
            events = events.filter(created_at__gte=_since(since))
        if ids:
            events = events.filter(pk__in=ids)
        if failed:
            events = events.exclude(error="")
        counts = run_job(JobRun.WEBHOOK_REPLAY, lambda: replay(events), by_hand=True)  # kept as a run, for Server
        n = counts["handled"] + counts["failed"]
        self.stdout.write(f"{n} call{'s' if n != 1 else ''} run again: {counts['handled']} handled, {counts['failed']} still failing.")
