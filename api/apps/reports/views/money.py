from django.db.models import Count, F, OuterRef, Prefetch, Q, Subquery, Sum
from drf_spectacular.utils import extend_schema

from apps.finance import services
from apps.finance.models import Account, DrawerClose, MoneyMove, Reconciliation
from apps.gyms.models import Branch

from ..period import LIST_MAX, PARAMS, Period, ReportView
from ..serializers import Money


def accounts_for(p: Period):
    """The accounts a report covers, with their balances at the period's two ends: every account the gym had by the
    last day, or one branch's cash and the bank account it uses, shown whole even when other branches share it."""
    qs = Account.objects.filter(gym=p.gym, opened_on__lte=p.last)
    if p.branch is not None:
        mine = Account.objects.filter(Q(kind=Account.CASH, branch_id=p.branch) | Q(kind=Account.BANK, links__branch_id=p.branch))
        qs = qs.filter(pk__in=mine.values("pk"))
    return services.with_period(qs, p.gym, p.first, p.last)


@extend_schema(parameters=PARAMS, responses=Money)
class MoneyView(ReportView):
    """Cash and bank: each account's balance before and after the days, what came in and went out, the money moved
    between them, the desk's cash counts and each bank account's latest reconciliation. Money moves are never income
    or spending, so the other reports leave them out."""

    trend = False

    def report(self, p: Period) -> dict:
        accounts = self._accounts(p)
        ids = [a.pk for a in accounts]
        total = lambda kind, end: sum(getattr(a, end) for a in accounts if kind in (None, a.kind))  # noqa: E731
        return {
            "totals": {"cash_opening_paise": total(Account.CASH, "opening_paise"), "cash_closing_paise": total(Account.CASH, "closing_paise"),
                       "bank_opening_paise": total(Account.BANK, "opening_paise"), "bank_closing_paise": total(Account.BANK, "closing_paise"),
                       "opening_paise": total(None, "opening_paise"), "closing_paise": total(None, "closing_paise")},
            "accounts": [self._account(a, p.branch) for a in accounts],
            "moves": self._moves(p, ids),
            "counts": self._counts(p),
        }

    @staticmethod
    def _accounts(p: Period) -> list[Account]:
        """Cash first, then bank, by name. A deactivated account that held and moved nothing in these days is left out."""
        latest = Reconciliation.objects.filter(account=OuterRef("pk"), up_to__lte=p.last).order_by("-up_to", "-id").values("pk")[:1]
        rows = (accounts_for(p).annotate(latest_check=Subquery(latest)).select_related("branch")
                .prefetch_related(Prefetch("branches", queryset=Branch.objects.order_by("name"))))
        rows = [a for a in rows if a.is_active or a.opening_paise or a.in_paise or a.out_paise]
        checks = Reconciliation.objects.filter(pk__in=[a.latest_check for a in rows if a.latest_check]).select_related("by__user")
        found = {r.pk: r for r in checks}
        for a in rows:
            a.reconciliation = found.get(a.latest_check)
        return sorted(rows, key=lambda a: (a.kind != Account.CASH, a.label.lower(), a.pk))

    @staticmethod
    def _account(a: Account, branch: int | None) -> dict:
        c = a.reconciliation
        return {
            "id": a.pk, "name": a.label, "kind": a.kind, "is_active": a.is_active, "opened_on": a.opened_on,
            "shared_with": [b.name for b in a.branches.all() if b.pk != branch] if a.kind == Account.BANK else [],
            "opening_paise": a.opening_paise, "closing_paise": a.closing_paise, "in_paise": a.in_paise, "out_paise": a.out_paise,
            "moved_in_paise": a.moved_in_paise, "moved_out_paise": a.moved_out_paise,
            "reconciled": {"up_to": c.up_to, "bank_balance_paise": c.bank_balance_paise, "by_name": c.by.user.name} if c else None,
        }

    @staticmethod
    def _moves(p: Period, ids: list[int]) -> dict:
        """Money moved in these days. For one branch, the moves in or out of its accounts, each once."""
        moves = MoneyMove.objects.filter(gym=p.gym, voided=False, moved_on__range=(p.first, p.last))
        if p.branch is not None:
            moves = moves.filter(Q(from_account__in=ids) | Q(to_account__in=ids))
        rows = list(moves.select_related("from_account__branch", "to_account__branch").order_by("-moved_on", "-id")[:LIST_MAX])
        return {"count": len(rows) if len(rows) < LIST_MAX else moves.count(), "rows": [
            {"id": m.pk, "on": m.moved_on, "kind": m.kind, "from_name": m.from_account.label if m.from_account else None,
             "to_name": m.to_account.label if m.to_account else None, "amount_paise": m.amount_paise, "note": m.note}
            for m in rows
        ]}

    @staticmethod
    def _counts(p: Period) -> dict:
        """The desk's cash counts in these days, what they came to, and how many differences still wait for an admin."""
        closes = DrawerClose.objects.filter(gym=p.gym, day__range=(p.first, p.last), **p.at("branch_id"))
        short, over = Q(counted_paise__lt=F("expected_paise")), Q(counted_paise__gt=F("expected_paise"))
        agg = closes.aggregate(
            n=Count("id"), short=Sum(F("expected_paise") - F("counted_paise"), filter=short), over=Sum(F("counted_paise") - F("expected_paise"), filter=over),
            open=Count("id", filter=(short | over) & Q(settled_at__isnull=True)),
        )
        rows = closes.select_related("branch").order_by("-day", "branch__name")[:LIST_MAX]
        return {"count": agg["n"], "short_paise": agg["short"] or 0, "over_paise": agg["over"] or 0, "to_settle": agg["open"], "rows": [
            {"id": c.pk, "day": c.day, "branch_name": c.branch.name, "counted_paise": c.counted_paise, "expected_paise": c.expected_paise,
             "difference_paise": c.difference_paise, "settled": c.settled_at is not None}
            for c in rows
        ]}
