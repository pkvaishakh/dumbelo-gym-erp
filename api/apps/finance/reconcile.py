"""Checking a bank account against the bank's own statement: tick what the bank shows, then mark it reconciled up to a
day at the bank's balance. Reconciled entries are locked (`services.before_change`) until an admin un-reconciles one."""
from datetime import date

from django.db import transaction
from django.db.models import Q

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.expenses.models import Expense
from apps.members.models import Payment, Refund

from .models import Account, MoneyMove, Reconciliation, StatementTick
from .services import _lock, cleared


def _bank(account: Account) -> None:
    if account.kind != Account.BANK:
        raise RuleBroken("not_a_bank_account", "Only a bank account is checked against a bank's statement")


def _on_statement(account: Account, kind: str, entry_id: int) -> tuple[date, int]:
    """The entry's day and signed amount on this account's statement, or a refusal when it isn't on it."""
    gym = account.gym
    if kind == StatementTick.PAYMENT:
        p = Payment.objects.filter(pk=entry_id, account=account, voided=False).first()
        if p:
            return clock.local(gym, p.taken_at).date(), p.amount_paise
    elif kind == StatementTick.EXPENSE:
        e = Expense.objects.filter(pk=entry_id, account=account).first()
        if e:
            return e.spent_on, -e.amount_paise
    elif kind == StatementTick.REFUND:
        r = Refund.objects.filter(pk=entry_id, account=account, voided=False).first()
        if r:
            return clock.local(gym, r.refunded_at).date(), -r.amount_paise
    elif kind == StatementTick.MOVE:
        m = MoneyMove.objects.filter(Q(from_account=account) | Q(to_account=account), pk=entry_id, voided=False).first()
        if m:
            return m.moved_on, m.amount_paise if m.to_account_id == account.pk else -m.amount_paise
    raise RuleBroken("not_on_statement", "That entry isn't on this account's statement any more. Reload it.")


@transaction.atomic
def tick(account: Account, entries: list[tuple[str, int]], *, ticked: bool, by) -> None:
    """Mark entries as on the bank's statement, or not. A reconciled entry stays ticked until it is un-reconciled."""
    _bank(account)
    if ticked:
        have = set(StatementTick.objects.filter(account=account, kind__in={k for k, _ in entries}).filter(
            entry_id__in=[i for _, i in entries]).values_list("kind", "entry_id"))
        fresh = []
        for kind, entry_id in entries:
            if (kind, entry_id) not in have:
                on, amount = _on_statement(account, kind, entry_id)
                fresh.append(StatementTick(gym_id=account.gym_id, account=account, kind=kind, entry_id=entry_id, on=on, amount_paise=amount, ticked_by=by))
        StatementTick.objects.bulk_create(fresh)
        return
    q = Q()
    for kind, entry_id in entries:
        q |= Q(kind=kind, entry_id=entry_id)
    ticks = StatementTick.objects.select_for_update().filter(q, account=account)
    if any(t.reconciliation_id for t in ticks):
        raise RuleBroken("reconciled", "That one is reconciled. Un-reconcile it first.")
    ticks.delete()


@transaction.atomic
def reconcile(account: Account, *, up_to: date, bank_balance_paise: int, by) -> Reconciliation:
    """The bank says the account held `bank_balance_paise` at the end of `up_to`: it must match the opening balance and
    the ticked entries up to then. Those ticks are then locked; entries not ticked are still on their way to the bank."""
    _bank(account)
    _lock(account)  # one reconciliation at a time per account
    if up_to < account.opened_on:
        raise RuleBroken("before_opened", f"{account.label} was added on {clock.date_label(account.opened_on)}. Pick that day or later.")
    if up_to > clock.today(account.gym):
        raise RuleBroken("future", "Pick today or an earlier day")
    last = Reconciliation.objects.filter(account=account).first()
    if last and up_to < last.up_to:
        raise RuleBroken("before_last", f"It's reconciled up to {clock.date_label(last.up_to)} already. Pick that day or later.")
    ticks = StatementTick.objects.select_for_update().filter(account=account, on__lte=up_to)
    list(ticks)  # hold them: an entry corrected meanwhile waits, then finds its tick reconciled
    if (ours := cleared(account, up_to)) != bank_balance_paise:
        gap = bank_balance_paise - ours
        raise RuleBroken("not_matched", f"Your ticked entries up to {clock.date_label(up_to)} come to {rupees(ours)}, {rupees(abs(gap))} "
                                        f"{'less' if gap > 0 else 'more'} than the bank's. Tick what's on the bank's statement, or add what's "
                                        "missing (bank charges are a withdrawal).")
    rec = Reconciliation.objects.create(gym_id=account.gym_id, account=account, up_to=up_to, bank_balance_paise=bank_balance_paise, by=by)
    ticks.filter(reconciliation__isnull=True).update(reconciliation=rec)
    return rec


@transaction.atomic
def unreconcile(account: Account, kind: str, entry_id: int) -> StatementTick:
    """Unlock one reconciled entry so it can be corrected or voided. It stays ticked until it changes."""
    t = StatementTick.objects.select_for_update().filter(account=account, kind=kind, entry_id=entry_id, reconciliation__isnull=False).first()
    if t is None:
        raise RuleBroken("not_reconciled", "That entry isn't reconciled")
    t.reconciliation = None
    t.save(update_fields=["reconciliation", "updated_at"])
    return t
