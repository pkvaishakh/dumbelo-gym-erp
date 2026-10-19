"""Write the Dumbelo invoices due today, the same as the hourly job: `python manage.py write_invoices`.

    python manage.py write_invoices --day 2026-11-01   # a billing day the worker missed

Safe to run again: a gym whose month already has an invoice is skipped.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.billing.tasks import write_invoices


class Command(BaseCommand):
    help = "Write each active gym's Dumbelo invoice on its billing day (the hourly job, by hand)."

    def add_arguments(self, parser):
        parser.add_argument("--day", default="", help="YYYY-MM-DD: bill the gyms whose billing day this was. Today on each gym's clock if left out")

    def handle(self, *args, day="", **kw):
        try:
            date.fromisoformat(day) if day else None
        except ValueError:
            raise CommandError("Give --day as YYYY-MM-DD")
        n = write_invoices(day or None, by_hand=True)  # in this process, kept as a run by hand
        self.stdout.write(f"{n} invoice{'s' if n != 1 else ''} written.")
