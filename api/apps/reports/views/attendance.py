from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema

from apps.attendance.services import count_by_session_over
from apps.gyms.models import Branch

from ..period import PARAMS, Period, ReportView
from ..serializers import Attendance

MEMBER, STAFF = Q(member__isnull=False), Q(member__isnull=True)


@extend_schema(parameters=PARAMS, responses=Attendance)
class AttendanceView(ReportView):
    """Check-ins by day, session and branch, members and staff apart. Check-in time only: nobody's time inside."""

    def report(self, p: Period) -> dict:
        _, members_before = p.compare("checkins", only=MEMBER)
        totals, sessions = count_by_session_over(p.checkins, p.gym)
        days = {d: (m, s) for d, m, s in self._split(p.checkins, "local_date")}
        return {
            "totals": totals,
            "before": {"member": members_before},
            "series": [{"date": d, "member": days.get(d, (0, 0))[0], "staff": days.get(d, (0, 0))[1]} for d in p.every_day()],
            "sessions": sessions,
            "branches": self._branches(p) if p.branch is None else [],
        }

    @staticmethod
    def _split(qs, key: str):
        """(key, member check-ins, staff check-ins) rows."""
        return qs.values_list(key).annotate(m=Count("id", filter=MEMBER), s=Count("id", filter=STAFF)).order_by()

    def _branches(self, p: Period) -> list[dict]:
        per = {b: (m, s) for b, m, s in self._split(p.checkins, "branch_id")}
        return [{"id": b.pk, "name": b.name, "member": per.get(b.pk, (0, 0))[0], "staff": per.get(b.pk, (0, 0))[1]}
                for b in Branch.objects.filter(gym=p.gym, is_active=True).order_by("name")]
