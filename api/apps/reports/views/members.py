from collections import Counter
from datetime import timedelta

from django.db.models import Exists, OuterRef
from drf_spectacular.utils import extend_schema

from apps.gyms.models import Branch
from apps.members.models import STATUSES, Member, Subscription

from ..period import PARAMS, Period, ReportView, counted
from ..serializers import Members

ACTIVE = ("active", "expiring", "due")


@extend_schema(parameters=PARAMS, responses=Members)
class MembersView(ReportView):
    """New members, renewals and plans that ran out without one, by day and branch, and every member's status on the
    last day."""

    def report(self, p: Period) -> dict:
        new, new_before = p.compare("joined")
        renewed, renewed_before = p.compare("renewals")
        days = p.daily("joined")
        statuses, active = self._statuses(p)
        return {
            "totals": {"new": new, "renewals": renewed, "lapsed": self._lapsed(p)},
            "before": {"new": new_before, "renewals": renewed_before},
            "series": [{"date": d, "new": days.get(d, 0)} for d in p.every_day()],
            "statuses": {"total": sum(statuses.values()), **{s: statuses.get(s, 0) for s in STATUSES}},
            "branches": self._branches(p, active) if p.branch is None else [],
        }

    @staticmethod
    def _lapsed(p: Period) -> int:
        """Members whose plan ran out in these days (its last day was the day before one of them) and who have no
        later plan."""
        later = Subscription.objects.filter(member=OuterRef("member"), cancelled=False, starts__gt=OuterRef("starts"))
        ended = Subscription.objects.filter(
            member__gym=p.gym, member__is_archived=False, cancelled=False, ends__range=(p.first - timedelta(days=1), p.last - timedelta(days=1)),
            **p.at("member__home_branch_id"),
        )
        return ended.filter(~Exists(later)).values("member").distinct().count()

    @staticmethod
    def _statuses(p: Period) -> tuple[Counter, Counter]:
        """Every member's status on the last day, and each branch's active ones. Counted in Python, as on Home: a
        status follows plan dates, freezes and what is owed (`Member.status`), which SQL can't say; it is two queries
        for any number of members. What is owed is as of now: payments aren't replayed to the last day."""
        members = Member.objects.filter(gym=p.gym, is_archived=False, joined_on__lte=p.last, **p.at("home_branch_id")).with_totals()
        statuses, active = Counter(), Counter()
        for m in members:
            status = m.status(p.last)
            statuses[status] += 1
            if status in ACTIVE:
                active[m.home_branch_id] += 1
        return statuses, active

    @staticmethod
    def _branches(p: Period, active: Counter) -> list[dict]:
        new, renewed = counted(p.joined, "home_branch_id"), counted(p.renewals, "member__home_branch_id")
        return [{"id": b.pk, "name": b.name, "new": new.get(b.pk, 0), "renewals": renewed.get(b.pk, 0), "active": active[b.pk]}
                for b in Branch.objects.filter(gym=p.gym, is_active=True).order_by("name")]
