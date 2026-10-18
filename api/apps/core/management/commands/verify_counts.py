"""How many rows a gym has, to check a restored copy of the database against the live one (docs/operations.md).

    python manage.py verify_counts --gym rackline-fitness
    python manage.py verify_counts --gym rackline-fitness --until 2026-10-19T03:30Z   # rows written by then

Members, payments and check-ins are never deleted (archived, voided), so the rows a gym had at a moment can only
grow after it: run with `--until` set to the copy's restore time, on both databases, and the counts must match.
The money line is what was recorded then; a payment corrected or voided since changes it on the live side only.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q, Sum

from apps.attendance.models import CheckIn
from apps.core import clock
from apps.core.money import rupees
from apps.gyms.models import Gym
from apps.members.models import Member, Payment


def counts(gym: Gym, until=None) -> dict[str, int]:
    """The gym's members, payments (and their total, and how many are voided) and check-ins, written by `until`."""
    by = Q(created_at__lte=until) if until else Q()
    members = Member.objects.filter(by, gym=gym).aggregate(n=Count("id"), n_archived=Count("id", filter=Q(is_archived=True)))
    payments = Payment.objects.filter(by, gym=gym).aggregate(n=Count("id"), n_voided=Count("id", filter=Q(voided=True)),
                                                             paise=Sum("amount_paise", filter=Q(voided=False)))
    return {
        "members": members["n"], "archived": members["n_archived"],
        "payments": payments["n"], "voided": payments["n_voided"], "paid_paise": payments["paise"] or 0,
        "checkins": CheckIn.objects.filter(by, gym=gym).count(),
    }


class Command(BaseCommand):
    help = "Count a gym's members, payments and check-ins, to compare a restored database with the live one."

    def add_arguments(self, parser):
        parser.add_argument("--gym", required=True, action="append", dest="gyms", help="The gym's short name (slug); give it again for more")
        parser.add_argument("--until", default="", help="Only rows written by then: the restore time, e.g. 2026-10-19T03:30Z (UTC unless it says)")

    def handle(self, *args, gyms=(), until="", **kw):
        try:
            at = clock.moment(until) if until else None
        except ValueError:
            raise CommandError("Give --until as YYYY-MM-DD or YYYY-MM-DDTHH:MM") from None
        found = {g.slug: g for g in Gym.objects.filter(slug__in=gyms)}
        if missing := [s for s in gyms if s not in found]:
            raise CommandError(f"No gym with the short name {', '.join(missing)} in this database.")
        if at:
            self.stdout.write(f"Rows written by {at.isoformat()}")
        for slug in gyms:
            c = counts(found[slug], at)
            self.stdout.write(f"{slug}  {found[slug].name}")
            self.stdout.write(f"  members    {c['members']:>8}   {c['archived']} archived")
            self.stdout.write(f"  payments   {c['payments']:>8}   {c['voided']} voided, {rupees(c['paid_paise']).removeprefix('₹')} rupees recorded")  # a Windows console has no ₹
            self.stdout.write(f"  check-ins  {c['checkins']:>8}")
