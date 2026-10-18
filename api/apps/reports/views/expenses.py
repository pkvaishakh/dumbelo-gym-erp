from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema

from apps.core import clock
from apps.expenses.services import bills_due
from apps.payroll.services import salaries_owed

from ..period import LIST_MAX, PARAMS, Period, ReportView, branch_names, ranked, summed
from ..serializers import CATEGORY, METHOD, Expenses


@extend_schema(parameters=PARAMS, responses=Expenses)
class ExpensesView(ReportView):
    """Money spent: by day, category, method and branch; the bills paid from Dues and the salaries paid, which are
    expenses too and so inside the totals; and what the gym still owes now."""

    def report(self, p: Period) -> dict:
        spent, spent_before = p.compare("expenses", "amount_paise")
        days = p.daily("expenses", "amount_paise")
        categories = p.expenses.values_list("category").annotate(t=Sum("amount_paise"), n=Count("id")).order_by()
        return {
            "totals": {"spent_paise": spent, "count": sum(n for _, _, n in categories)},
            "before": {"spent_paise": spent_before},
            "series": [{"date": d, "spent_paise": days.get(d, 0)} for d in p.every_day()],
            "by_category": ranked({c: t for c, t, _ in categories}, CATEGORY.get),
            "by_method": ranked(summed(p.expenses, "method"), METHOD.get),
            "by_branch": ranked(summed(p.expenses, "branch_id"), branch_names(p.gym).get) if p.branch is None else [],
            "bills": self._bills(p),
            "salaries": self._salaries(p),
            "owed": self._owed(p),
        }

    @staticmethod
    def _bills(p: Period) -> dict:
        """Recurring bills paid from Dues in these days: each payment wrote one of these expenses."""
        bills = p.expenses.filter(due__isnull=False)
        agg = bills.aggregate(n=Count("id"), t=Sum("amount_paise"))
        rows = bills.select_related("due__recurring").order_by("-spent_on", "-id")[:LIST_MAX]
        return {"count": agg["n"], "paid_paise": agg["t"] or 0, "rows": [
            {"id": e.pk, "name": e.due.recurring.name, "due_on": e.due.due_on, "paid_on": e.spent_on, "amount_paise": e.amount_paise} for e in rows
        ]}

    @staticmethod
    def _salaries(p: Period) -> dict:
        """Salaries paid in these days, by person: each salary payment wrote one of these expenses."""
        paid = p.expenses.filter(salary_payment__isnull=False)
        people = (paid.values("salary_payment__payslip__staff", "salary_payment__payslip__staff__user__name")
                  .annotate(t=Sum("amount_paise"), n=Count("id")).order_by("-t", "salary_payment__payslip__staff__user__name"))
        rows = [{"id": x["salary_payment__payslip__staff"], "name": x["salary_payment__payslip__staff__user__name"], "paid_paise": x["t"],
                 "payments": x["n"]} for x in people]
        return {"count": sum(r["payments"] for r in rows), "paid_paise": sum(r["paid_paise"] for r in rows), "people": rows}

    @staticmethod
    def _owed(p: Period) -> dict:
        """What the gym owes now, the same figures as Home and Dues. Bills as Home and Dues last wrote them down: a
        report only reads, so it never writes the dates (`sync_dues`) itself."""
        bills, salaries = bills_due(p.gym, clock.today(p.gym), p.branch), salaries_owed(p.gym, p.branch)
        return {"bills": bills["count"], "overdue_bills": bills["overdue"], "bills_paise": bills["total_paise"],
                "salaries": salaries["count"], "salaries_paise": salaries["total_paise"]}
