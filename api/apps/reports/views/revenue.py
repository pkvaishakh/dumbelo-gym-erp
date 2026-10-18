from drf_spectacular.utils import extend_schema

from apps.core import clock
from apps.members.models import Member

from ..period import LIST_MAX, PARAMS, Period, ReportView, branch_names, net, ranked, summed
from ..serializers import METHOD, Revenue


@extend_schema(parameters=PARAMS, responses=Revenue)
class RevenueView(ReportView):
    """Money taken less money given back: by day, plan, method and branch, the refunds themselves, and what members
    owe now. A refund counts against revenue on the day it's given, as on Home."""

    def report(self, p: Period) -> dict:
        taken, taken_before = p.compare("payments", "amount_paise")
        given, given_before = p.compare("refunds", "amount_paise")
        days = net(p.daily("payments", "amount_paise"), p.daily("refunds", "amount_paise"))
        refunds = self._refunds(p)
        members = Member.objects.filter(gym=p.gym, is_archived=False, **p.at("home_branch_id"))
        by = lambda key: net(summed(p.payments, key), summed(p.refunds, key))  # noqa: E731
        return {
            "totals": {"revenue_paise": taken - given, "collected_paise": taken, "refunds_paise": given,
                       "refunds": len(refunds) if len(refunds) < LIST_MAX else p.refunds.count()},
            "before": {"revenue_paise": taken_before - given_before},
            "series": [{"date": d, "revenue_paise": days.get(d, 0)} for d in p.every_day()],
            "by_plan": ranked(by("subscription__plan__name"), lambda name: name or "Other payments"),
            "by_method": ranked(by("method"), METHOD.get),
            "by_branch": ranked(by("branch_id"), branch_names(p.gym).get) if p.branch is None else [],
            "refund_list": refunds,
            "dues": members.owing(),
        }

    @staticmethod
    def _refunds(p: Period) -> list[dict]:
        rows = p.refunds.select_related("member", "subscription__plan", "branch").order_by("-refunded_at", "-id")[:LIST_MAX]
        return [
            {"id": r.pk, "on": clock.local(p.gym, r.refunded_at).date(), "member": r.member_id, "member_name": r.member.name,
             "plan": r.subscription.plan.name, "method": r.method, "branch_name": r.branch.name, "amount_paise": r.amount_paise, "reason": r.reason}
            for r in rows
        ]
