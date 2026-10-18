"""Balances, the branches each bank account serves, and moving money between accounts."""
from datetime import date, timedelta

from django.db import transaction
from django.db.models import BigIntegerField, F, OuterRef, Prefetch, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.money import rupees
from apps.expenses.models import Expense
from apps.gyms.models import Branch
from apps.members.models import Payment

from .models import Account, BranchAccount, MoneyMove


def _total(model, fk: str, **only):
    """The sum of `amount_paise` of `model` rows pointing at the outer account through `fk`, 0 when there are none."""
    rows = model.objects.filter(**{fk: OuterRef("pk")}, **only).order_by().values(fk).annotate(t=Sum("amount_paise")).values("t")
    return Coalesce(Subquery(rows, output_field=BigIntegerField()), Value(0), output_field=BigIntegerField())


def with_balance(qs):
    """Each account with what moved it and its balance, in the same query: lists never ask per row.

    A voided payment or money move never happened; an expense is removed outright, so it leaves the balance too.
    """
    return qs.annotate(
        collected_paise=_total(Payment, "account", voided=False),
        spent_paise=_total(Expense, "account"),
        moved_in_paise=_total(MoneyMove, "to_account", voided=False),
        moved_out_paise=_total(MoneyMove, "from_account", voided=False),
    ).annotate(balance_paise=F("opening_balance_paise") + F("collected_paise") - F("spent_paise") + F("moved_in_paise") - F("moved_out_paise"))


def listed(gym):
    """The gym's accounts as every screen shows them: balance, branch, and the branches a bank account serves."""
    return with_balance(Account.objects.filter(gym=gym)).select_related("branch").prefetch_related(
        Prefetch("branches", queryset=Branch.objects.order_by("name")))


def balance_of(account: Account) -> int:
    """One account's balance, read fresh (call it under the account's lock when money leaves it)."""
    return with_balance(Account.objects.filter(pk=account.pk)).values_list("balance_paise", flat=True).get()


def _lock(*accounts: Account | None) -> None:
    """Hold the accounts money leaves or enters until the transaction ends, always in id order, so two moves between
    the same pair of accounts wait for each other instead of deadlocking. Refuses an account deactivated meanwhile:
    the caller's copy may be older than the lock."""
    ids = sorted({a.pk for a in accounts if a is not None})
    live = dict(Account.objects.select_for_update().filter(pk__in=ids).order_by("pk").values_list("pk", "is_active"))
    for a in accounts:
        if a is not None and not live[a.pk]:
            raise RuleBroken("inactive", f"{a.label} is deactivated. Reactivate it first.")


@transaction.atomic
def set_branches(account: Account, branches: list[Branch]) -> dict[int, int | None]:
    """The branches that use this bank account, exactly. A branch that used another account moves here (a branch has
    one bank account); a branch taken off is left with none. Answers {branch id: account it used before}, for the
    audit log, for every branch that changed."""
    if account.kind != Account.BANK:
        raise RuleBroken("not_a_bank_account", "Only a bank account is given to branches")
    wanted = {b.pk for b in branches}
    if wanted and not account.is_active:
        raise RuleBroken("inactive", f"{account.label} is deactivated. Reactivate it first.")
    links = {link.branch_id: link for link in BranchAccount.objects.select_for_update().filter(Q(account=account) | Q(branch_id__in=wanted))}
    changed: dict[int, int | None] = {}
    for branch_id, link in links.items():
        if branch_id not in wanted:  # taken off this account
            changed[branch_id] = account.pk
            link.delete()
        elif link.account_id != account.pk:  # moves here from another account
            changed[branch_id] = link.account_id
            link.account = account
            link.save(update_fields=["account"])
    fresh = [BranchAccount(branch_id=b, account=account) for b in wanted - links.keys()]
    BranchAccount.objects.bulk_create(fresh)
    changed.update({link.branch_id: None for link in fresh})
    return changed


@transaction.atomic
def set_branch_account(branch: Branch, account: Account | None) -> int | None:
    """The one bank account a branch uses from now on, or none. Answers the account it used before."""
    if account is not None and account.kind != Account.BANK:
        raise RuleBroken("not_a_bank_account", "Pick a bank account")
    if account is not None and not account.is_active:
        raise RuleBroken("inactive", f"{account.label} is deactivated. Reactivate it first.")
    link = BranchAccount.objects.select_for_update().filter(branch=branch).first()
    before = link.account_id if link else None
    if account is None:
        if link:
            link.delete()
    elif link:
        link.account = account
        link.save(update_fields=["account"])
    else:
        BranchAccount.objects.create(branch=branch, account=account)
    return before


@transaction.atomic
def deactivate(account: Account) -> list[int]:
    """Stop using an account. It must be empty, so no money drops out of the totals; branches that used it are left
    with no bank account until they're given another. Answers those branches' ids."""
    if not account.is_active:
        raise RuleBroken("inactive", f"{account.label} is already deactivated")
    _lock(account)
    if (left := balance_of(account)) != 0:
        raise RuleBroken("not_empty", f"{account.label} holds {rupees(left)}. Move it to another account first.")
    branches = list(account.links.values_list("branch_id", flat=True))
    account.links.all().delete()
    account.is_active = False
    account.save(update_fields=["is_active", "updated_at"])
    return branches


@transaction.atomic
def move(gym, *, kind: str, amount_paise: int, moved_on: date, by, from_account: Account | None = None,
         to_account: Account | None = None, note: str = "") -> MoneyMove:
    """Put money in, take it out, or move it between two accounts. Money leaving an account can't be more than it
    holds, checked under the account's lock so two moves at once can't both spend the same rupees."""
    need = {MoneyMove.DEPOSIT: (False, True), MoneyMove.WITHDRAWAL: (True, False), MoneyMove.TRANSFER: (True, True)}[kind]
    if (from_account is not None, to_account is not None) != need:
        raise RuleBroken("accounts_invalid", "Pick where the money comes from and where it goes")
    if from_account is not None and from_account == to_account:
        raise RuleBroken("same_account", "Pick two different accounts")
    if amount_paise <= 0:
        raise RuleBroken("amount_invalid", "Enter an amount above zero")
    for a in (from_account, to_account):
        if a is not None and moved_on < a.opened_on:  # its opening balance already counts what moved before then
            raise RuleBroken("before_opened", f"{a.label} was added on {clock.date_label(a.opened_on)}. Pick that day or later.")
    _lock(from_account, to_account)
    if from_account is not None and (held := balance_of(from_account)) < amount_paise:
        raise RuleBroken("not_enough", f"{from_account.label} holds {rupees(max(held, 0))}. Move that or less.")
    return MoneyMove.objects.create(gym=gym, kind=kind, from_account=from_account, to_account=to_account, amount_paise=amount_paise,
                                    moved_on=moved_on, note=note, created_by=by)


@transaction.atomic
def void(m: MoneyMove, reason: str) -> MoneyMove:
    """Undo a money move that was wrong. Money it brought into an account leaves again, so that account must still
    hold it: undoing a deposit that was already spent would leave less than nothing. Both accounts must be in use:
    money put back into a deactivated account would sit where no one moves it."""
    _lock(m.from_account, m.to_account)
    m = MoneyMove.objects.select_for_update(of=("self",)).select_related("to_account__branch").get(pk=m.pk)
    if m.voided:
        raise RuleBroken("voided", "This one is already voided")
    if m.to_account is not None and (held := balance_of(m.to_account)) < m.amount_paise:
        raise RuleBroken("not_enough", f"{m.to_account.label} holds {rupees(max(held, 0))}, less than this brought in. Move money back to it first.")
    m.voided, m.void_reason = True, reason
    m.save(update_fields=["voided", "void_reason", "updated_at"])
    return m


def overview(gym) -> dict:
    """Money across the gym, each account counted once however many branches share it, and each branch's cash and
    bank account. A shared account shows under each branch that uses it, with the others named, never added twice."""
    accounts = list(listed(gym))
    # Every account, deactivated ones too: they hold nothing when deactivated, but a payment voided or an expense
    # removed later still moves their balance, and that money is the gym's.
    cash = sum(a.balance_paise for a in accounts if a.kind == Account.CASH)
    bank = sum(a.balance_paise for a in accounts if a.kind == Account.BANK)
    live = [a for a in accounts if a.is_active]
    cash_at = {a.branch_id: a for a in live if a.kind == Account.CASH}
    bank_of = {b.pk: a for a in live if a.kind == Account.BANK for b in a.branches.all()}

    def brief(a: Account | None, branch_id: int) -> dict | None:
        if a is None:
            return None
        shared = [b.name for b in a.branches.all() if b.pk != branch_id] if a.kind == Account.BANK else []
        return {"id": a.pk, "name": a.label, "balance_paise": a.balance_paise, "shared_with": shared}

    branches = [
        {"id": b.pk, "name": b.name, "cash": brief(cash_at.get(b.pk), b.pk), "bank": brief(bank_of.get(b.pk), b.pk)}
        for b in Branch.objects.filter(gym=gym, is_active=True)
    ]
    return {"totals": {"cash_paise": cash, "bank_paise": bank, "total_paise": cash + bank}, "branches": branches, "accounts": accounts}


def statement(account: Account, month: date) -> dict:
    """One account's month, entry by entry, to check against the bank's statement or the drawer: every payment taken
    in, expense paid out and money moved, oldest first, with the balance after each. It opens with the balance the
    day before and closes with the balance after the last day, so a month ending today closes on `balance_of`.
    Voided payments and moves are left out: they never happened."""
    gym = account.gym
    first, last = max(month, account.opened_on), min(clock.add_months(month, 1) - timedelta(days=1), clock.today(gym))
    start, end = clock.day_bounds(gym, first)[0], clock.day_bounds(gym, last)[1]
    payments = Payment.objects.filter(account=account, voided=False)
    expenses = Expense.objects.filter(account=account)
    moves = MoneyMove.objects.filter(Q(from_account=account) | Q(to_account=account), voided=False)

    def total(qs, **before):
        return qs.filter(**before).aggregate(t=Sum("amount_paise"))["t"] or 0

    opening = (account.opening_balance_paise + total(payments, taken_at__lt=start) - total(expenses, spent_on__lt=first)
               + total(moves.filter(to_account=account), moved_on__lt=first) - total(moves.filter(from_account=account), moved_on__lt=first))
    entries = []
    if first <= last:
        for p in payments.filter(taken_at__gte=start, taken_at__lt=end).select_related("member"):
            entries.append((clock.local(gym, p.taken_at).date(), p.taken_at, {
                "kind": "payment", "id": p.pk, "member": p.member_id, "title": p.member.name,
                "meta": f"Payment by {p.get_method_display()}", "amount_paise": p.amount_paise}))
        for e in expenses.filter(spent_on__gte=first, spent_on__lte=last):
            entries.append((e.spent_on, e.created_at, {
                "kind": "expense", "id": e.pk, "member": None, "title": e.paid_to or e.get_category_display(),
                "meta": f"{e.get_category_display()} by {e.get_method_display()}", "amount_paise": -e.amount_paise}))
        for m in moves.filter(moved_on__gte=first, moved_on__lte=last).select_related("from_account__branch", "to_account__branch"):
            into = m.to_account_id == account.pk
            other = m.from_account if into else m.to_account
            title = {MoneyMove.DEPOSIT: "Deposit", MoneyMove.WITHDRAWAL: "Withdrawal"}.get(m.kind) or f"{'From' if into else 'To'} {other.label}"
            entries.append((m.moved_on, m.created_at, {
                "kind": "move", "id": m.pk, "member": None, "title": title, "meta": m.note or m.get_kind_display(),
                "amount_paise": m.amount_paise if into else -m.amount_paise}))
    entries.sort(key=lambda x: (x[0], x[1]))
    balance, rows = opening, []
    for on, _, row in entries:
        balance += row["amount_paise"]
        rows.append({**row, "on": on, "balance_paise": balance})
    return {
        "from": first, "to": last, "opening_paise": opening, "closing_paise": balance,
        "in_paise": sum(r["amount_paise"] for r in rows if r["amount_paise"] > 0),
        "out_paise": -sum(r["amount_paise"] for r in rows if r["amount_paise"] < 0), "entries": rows,
    }
