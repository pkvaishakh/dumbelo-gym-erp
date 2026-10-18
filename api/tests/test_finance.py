"""Cash in hand, bank accounts shared by branches, balances, and moving money between them."""
import threading
import time
from datetime import timedelta

import pytest
from django.db import connection, transaction

from apps.audit.models import AuditLog
from apps.core.errors import RuleBroken
from apps.expenses.models import Expense, RecurringExpense
from apps.expenses.services import sync_dues
from apps.finance import services
from apps.finance.models import Account, BranchAccount, MoneyMove
from apps.members.models import Payment
from apps.members.services import sell, take_payment
from tests.conftest import World

ACCOUNTS = "/api/accounts/"
MOVES = "/api/money-moves/"


def bank(w, name="HDFC current", number="50200012345678", opening=1_00_000_00, branches=()):
    a = Account.objects.create(gym=w.gym, kind="bank", name=name, bank_name="HDFC Bank", account_number=number, opening_balance_paise=opening,
                               opened_on=w.today, created_by=w.admin)
    BranchAccount.objects.bulk_create([BranchAccount(branch=b, account=a) for b in branches])
    return a


def cash(w, branch, opening=0):
    return Account.objects.create(gym=w.gym, kind="cash", branch=branch, opening_balance_paise=opening, opened_on=w.today, created_by=w.admin)


def paid(w, member_name, phone, method, paise=150000, branch=None):
    """A member at branch A (or `branch`) sold a monthly plan and paying `paise` by `method`."""
    m = w.new_member(member_name, phone, branch or w.a)
    sell(m, w.monthly, by=w.desk)
    return take_payment(m, paise, method, by=w.desk)


def balances(c):
    return {a["label"]: a["balance_paise"] for a in c.get(ACCOUNTS).json()}


def test_admin_adds_a_bank_account_shared_by_two_branches_and_cash_at_one(w):
    c = w.client(w.admin)
    r = c.post(ACCOUNTS, {"kind": "bank", "name": "HDFC current", "bank_name": "HDFC Bank", "account_number": "5020 0012 3456 78", "ifsc": "hdfc0001234",
                          "opening_balance_paise": 2_00_000_00, "branches": [w.a.id, w.b.id]}, format="json")
    assert r.status_code == 201, r.json()
    body = r.json()
    assert (body["label"], body["account_number"], body["ifsc"], body["balance_paise"], body["opened_on"]) == ("HDFC current", "50200012345678", "HDFC0001234", 2_00_000_00, w.today.isoformat())
    assert sorted(body["branch_names"]) == ["A", "B"] and body["is_active"] is True
    r = c.post(ACCOUNTS, {"kind": "cash", "branch": w.a.id, "opening_balance_paise": 5_000_00, "name": "ignored", "account_number": "1"}, format="json")
    assert r.status_code == 201, r.json()
    assert (r.json()["label"], r.json()["account_number"], r.json()["branches"]) == ("A cash", "", [])
    assert AuditLog.objects.filter(action="account.added").count() == 2
    assert AuditLog.objects.filter(action="account.branches_changed", object_id=str(body["id"])).exists()


def test_money_lands_in_the_branch_account_for_how_it_was_paid(w):
    hdfc, drawer = bank(w, branches=[w.a, w.b]), cash(w, w.a, opening=2_000_00)
    before = Payment.objects.get(member=w.member)  # taken before any account existed: it counts nowhere
    assert before.account is None
    upi = paid(w, "Ravi", "9811111111", "upi")
    note = paid(w, "Sita", "9811111112", "cash", paise=50000)
    at_b = paid(w, "Bina", "9811111113", "cash", branch=w.b)  # B has no cash account set up: untracked
    assert (upi.account, note.account, at_b.account) == (hdfc, drawer, None)
    c = w.client(w.admin)
    r = c.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 30000, "method": "cash", "spent_on": w.today.isoformat()}, format="json")
    assert r.status_code == 201 and Expense.objects.get(id=r.json()["id"]).account == drawer
    assert balances(c) == {"HDFC current": 1_00_000_00 + 150000, "A cash": 2_000_00 + 50000 - 30000}
    one = c.get(f"{ACCOUNTS}{drawer.id}/").json()
    assert (one["opening_balance_paise"], one["collected_paise"], one["spent_paise"], one["moved_in_paise"], one["moved_out_paise"]) == (2_000_00, 50000, 30000, 0, 0)


def test_a_voided_or_corrected_payment_follows_its_account(w):
    hdfc, drawer = bank(w, branches=[w.a]), cash(w, w.a)
    p = paid(w, "Ravi", "9811111111", "cash")
    c = w.client(w.admin)
    r = c.patch(f"/api/payments/{p.id}/", {"method": "upi", "reason": "Paid by UPI, typed as cash"}, format="json")
    assert r.status_code == 200, r.json()
    assert balances(c) == {"HDFC current": 1_00_000_00 + 150000, "A cash": 0}
    c.post(f"/api/payments/{p.id}/void/", {"reason": "Duplicate"}, format="json")
    assert balances(c)["HDFC current"] == 1_00_000_00
    e = Expense.objects.create(gym=w.gym, branch=w.a, category="other", amount_paise=10000, method="cash", created_by=w.admin, account=drawer)
    assert c.patch(f"/api/expenses/{e.id}/", {"method": "bank"}, format="json").status_code == 200
    e.refresh_from_db()
    assert e.account == hdfc


def test_bills_and_salaries_paid_come_out_of_the_branch_account(w):
    hdfc = bank(w, branches=[w.a])
    rule = RecurringExpense.objects.create(gym=w.gym, branch=w.a, name="Rent", category="rent", amount_paise=85_000_00, method="bank", frequency="monthly",
                                           starts=w.today, remind_days=3, created_by=w.admin)
    sync_dues(w.gym)
    c = w.client(w.admin)
    due = rule.dues.first()
    assert c.post(f"/api/expense-dues/{due.id}/pay/", {"amount_paise": 85_000_00, "method": "bank"}, format="json").status_code == 200
    assert Expense.objects.get(due=due).account == hdfc
    assert balances(c)["HDFC current"] == 1_00_000_00 - 85_000_00


def test_overview_counts_a_shared_account_once_and_names_who_shares_it(w):
    bank(w, branches=[w.a, w.b], opening=3_00_000_00)
    bank(w, name="ICICI reserve", number="000401234567", opening=50_000_00)  # used by no branch: still the gym's money
    cash(w, w.a, opening=4_000_00)
    cash(w, w.b, opening=6_000_00)
    off = bank(w, name="Old SBI", number="11112222333", opening=0)
    off.is_active = False
    off.save()
    r = w.client(w.admin).get(f"{ACCOUNTS}overview/").json()
    assert r["totals"] == {"cash_paise": 10_000_00, "bank_paise": 3_50_000_00, "total_paise": 3_60_000_00}
    rows = {b["name"]: b for b in r["branches"]}
    assert rows["A"]["bank"]["balance_paise"] == rows["B"]["bank"]["balance_paise"] == 3_00_000_00
    assert (rows["A"]["bank"]["shared_with"], rows["B"]["bank"]["shared_with"]) == (["B"], ["A"])
    assert (rows["A"]["cash"]["name"], rows["A"]["cash"]["balance_paise"]) == ("A cash", 4_000_00)
    assert len(r["accounts"]) == 5


def test_moving_a_branch_to_another_account_moves_new_money_only(w):
    hdfc = bank(w, branches=[w.a, w.b])
    c = w.client(w.admin)
    paid(w, "Bina", "9811111113", "upi", branch=w.b)
    icici = c.post(ACCOUNTS, {"kind": "bank", "name": "ICICI B", "bank_name": "ICICI", "account_number": "000401234567", "branches": [w.b.id]}, format="json").json()
    assert icici["branch_names"] == ["B"] and BranchAccount.objects.get(branch=w.b).account_id == icici["id"]
    later = paid(w, "Joy", "9811111114", "upi", branch=w.b)
    assert later.account_id == icici["id"]
    assert balances(c) == {"HDFC current": 1_00_000_00 + 150000, "ICICI B": 150000}
    moved = AuditLog.objects.get(action="account.branches_changed", object_id=str(icici["id"]))
    assert moved.after["moved"] == {str(w.b.id): hdfc.id}
    # From the branch side: A goes to ICICI too, then to no bank account at all.
    r = c.post(f"{ACCOUNTS}branch/", {"branch": w.a.id, "account": icici["id"]}, format="json")
    assert r.status_code == 200, r.json()
    assert {b["name"]: b["bank"]["name"] for b in r.json()["branches"]} == {"A": "ICICI B", "B": "ICICI B"}
    r = c.post(f"{ACCOUNTS}branch/", {"branch": w.a.id, "account": None}, format="json")
    assert {b["name"]: b["bank"] for b in r.json()["branches"]}["A"] is None
    assert AuditLog.objects.filter(action="branch.bank_account_changed", object_id=str(w.a.id)).count() == 2
    # Taking a branch off in the account's form leaves it with none.
    c.patch(f"{ACCOUNTS}{icici['id']}/", {"branches": []}, format="json")
    assert not BranchAccount.objects.filter(account_id=icici["id"]).exists()


def test_account_details_are_checked(w):
    c = w.client(w.admin)
    good = {"kind": "bank", "name": "HDFC", "bank_name": "HDFC Bank", "account_number": "50200012345678"}
    err = lambda r: (r.status_code, list(r.json()["error"].get("fields", {})))  # noqa: E731
    assert err(c.post(ACCOUNTS, {**good, "account_number": "12AB"}, format="json")) == (400, ["account_number"])
    assert err(c.post(ACCOUNTS, {**good, "ifsc": "HDFC123"}, format="json")) == (400, ["ifsc"])
    assert err(c.post(ACCOUNTS, {**good, "name": " "}, format="json")) == (400, ["name"])
    assert err(c.post(ACCOUNTS, {**good, "branch": w.a.id}, format="json")) == (400, ["branch"])
    assert err(c.post(ACCOUNTS, {**good, "opening_balance_paise": -1}, format="json")) == (400, ["opening_balance_paise"])
    first = c.post(ACCOUNTS, good, format="json").json()
    assert err(c.post(ACCOUNTS, good, format="json")) == (400, ["account_number"])
    assert err(c.post(ACCOUNTS, {"kind": "cash"}, format="json")) == (400, ["branch"])
    assert err(c.post(ACCOUNTS, {"kind": "cash", "branch": w.a.id, "branches": [w.b.id]}, format="json")) == (400, ["branches"])
    drawer = c.post(ACCOUNTS, {"kind": "cash", "branch": w.a.id}, format="json").json()
    assert err(c.post(ACCOUNTS, {"kind": "cash", "branch": w.a.id}, format="json")) == (400, ["branch"])
    r = c.patch(f"{ACCOUNTS}{drawer['id']}/", {"opening_balance_paise": 3_000_00, "branches": []}, format="json")  # the edit form's body
    assert r.status_code == 200 and r.json()["balance_paise"] == 3_000_00
    assert err(c.patch(f"{ACCOUNTS}{first['id']}/", {"kind": "cash"}, format="json")) == (400, ["kind"])
    r = c.patch(f"{ACCOUNTS}{first['id']}/", {"opening_balance_paise": 75_000_00, "name": "HDFC current"}, format="json")
    assert r.status_code == 200 and r.json()["balance_paise"] == 75_000_00
    log = AuditLog.objects.get(action="account.changed", object_id=str(first["id"]))
    assert (log.before["opening_balance_paise"], log.after["opening_balance_paise"]) == (0, 75_000_00)


def test_deposit_withdraw_and_transfer_update_both_balances(w):
    hdfc, drawer = bank(w, branches=[w.a]), cash(w, w.a, opening=20_000_00)
    c = w.client(w.admin)
    r = c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 15_000_00, "note": "Banked the week's cash"}, format="json")
    assert r.status_code == 201, r.json()
    assert (r.json()["from_name"], r.json()["to_name"], r.json()["from_kind"], r.json()["to_kind"], r.json()["moved_on"]) == ("A cash", "HDFC current", "cash", "bank", w.today.isoformat())
    assert c.post(MOVES, {"kind": "deposit", "to_account": hdfc.id, "amount_paise": 50_000_00, "note": "Owner's funds"}, format="json").status_code == 201
    assert c.post(MOVES, {"kind": "withdrawal", "from_account": hdfc.id, "amount_paise": 500_00, "note": "Bank charges"}, format="json").status_code == 201
    assert balances(c) == {"HDFC current": 1_00_000_00 + 15_000_00 + 50_000_00 - 500_00, "A cash": 5_000_00}
    assert AuditLog.objects.filter(action="money_move.added").count() == 3
    assert [m["kind"] for m in c.get(MOVES, {"account": drawer.id}).json()["results"]] == ["transfer"]


def test_transfers_are_never_income_or_spending(w):
    hdfc, drawer = bank(w, branches=[w.a]), cash(w, w.a, opening=20_000_00)
    c = w.client(w.admin)
    before = (c.get("/api/reports/summary/").json(), c.get("/api/reports/period/").json()["totals"])
    c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 15_000_00}, format="json")
    c.post(MOVES, {"kind": "deposit", "to_account": hdfc.id, "amount_paise": 10_000_00}, format="json")
    after = (c.get("/api/reports/summary/").json(), c.get("/api/reports/period/").json()["totals"])
    assert (after[0]["revenue"], after[0]["expenses_month_paise"]) == (before[0]["revenue"], before[0]["expenses_month_paise"])
    assert (after[1]["revenue_paise"], after[1]["expenses_paise"]) == (before[1]["revenue_paise"], before[1]["expenses_paise"])
    assert c.get("/api/expenses/totals/").json()["total_paise"] == 0


def test_money_moves_check_the_accounts_and_what_they_hold(w):
    hdfc, drawer = bank(w, branches=[w.a]), cash(w, w.a, opening=1_000_00)
    off = bank(w, name="Old SBI", number="11112222333", opening=0)
    off.is_active = False
    off.save()
    c = w.client(w.admin)
    code = lambda **kw: c.post(MOVES, kw, format="json").json()["error"]["code"]  # noqa: E731
    assert code(kind="transfer", from_account=drawer.id, to_account=hdfc.id, amount_paise=1_000_01) == "not_enough"
    assert code(kind="transfer", from_account=drawer.id, to_account=drawer.id, amount_paise=100) == "same_account"
    assert code(kind="deposit", from_account=drawer.id, to_account=hdfc.id, amount_paise=100) == "accounts_invalid"
    assert code(kind="withdrawal", to_account=hdfc.id, amount_paise=100) == "accounts_invalid"
    assert code(kind="deposit", to_account=off.id, amount_paise=100) == "inactive"
    assert code(kind="deposit", to_account=hdfc.id, amount_paise=0) == "invalid"
    tomorrow = (w.today + timedelta(days=1)).isoformat()
    assert code(kind="deposit", to_account=hdfc.id, amount_paise=100, moved_on=tomorrow) == "invalid"
    assert not MoneyMove.objects.exists()


def test_voiding_puts_the_money_back(w):
    hdfc, drawer = bank(w, branches=[w.a], opening=0), cash(w, w.a, opening=10_000_00)
    c = w.client(w.admin)
    move = c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 8_000_00}, format="json").json()
    spent = c.post(MOVES, {"kind": "withdrawal", "from_account": hdfc.id, "amount_paise": 5_000_00}, format="json").json()
    # HDFC holds ₹3,000 now: undoing the ₹8,000 it received would leave less than nothing.
    assert c.post(f"{MOVES}{move['id']}/void/", {"reason": "Wrong"}, format="json").json()["error"]["code"] == "not_enough"
    assert c.post(f"{MOVES}{spent['id']}/void/", {"reason": "Never drawn"}, format="json").json()["voided"] is True
    r = c.post(f"{MOVES}{move['id']}/void/", {"reason": "Typed twice"}, format="json")
    assert r.status_code == 200 and r.json()["void_reason"] == "Typed twice"
    assert balances(c) == {"HDFC current": 0, "A cash": 10_000_00}
    assert c.post(f"{MOVES}{move['id']}/void/", {"reason": "Again"}, format="json").json()["error"]["code"] == "voided"
    assert MoneyMove.objects.count() == 2 and AuditLog.objects.filter(action="money_move.voided").count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_two_withdrawals_at_once_cant_spend_the_same_money():
    w = World("race")
    drawer = cash(w, w.a, opening=1_000_00)
    start, out = threading.Barrier(2), []

    def withdraw():
        try:
            start.wait()
            services.move(w.gym, kind="withdrawal", from_account=drawer, amount_paise=800_00, moved_on=w.today, by=w.admin)
            out.append("ok")
        except RuleBroken as e:
            out.append(e.rule_code)
        finally:
            connection.close()

    threads = [threading.Thread(target=withdraw) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(out) == ["not_enough", "ok"] and services.balance_of(drawer) == 200_00


def _overlap(first, second):
    """Run `first` in a transaction that stays open a moment after it's done, and `second` while it's open: the
    worst timing for two desks at once."""
    started, out = threading.Event(), {}

    def run(name, fn, hold):
        try:
            with transaction.atomic():
                out[name] = fn()
                if hold:
                    started.set()
                    time.sleep(0.3)
        except RuleBroken as e:
            out[name] = e.rule_code
        finally:
            started.set()
            connection.close()

    one = threading.Thread(target=run, args=("first", first, True))
    two = threading.Thread(target=lambda: (started.wait(), run("second", second, False)))
    for t in (one, two):
        t.start()
    for t in (one, two):
        t.join()
    return out["first"], out["second"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_a_payment_while_its_drawer_is_deactivated_never_lands_in_it():
    w = World("race")
    drawer = cash(w, w.a)
    m = w.new_member("Ravi", "9811111111", w.a)
    sell(m, w.monthly, by=w.desk)
    deactivated, p = _overlap(lambda: services.deactivate(drawer), lambda: take_payment(m, 1_500_00, "cash", by=w.desk))
    assert deactivated == [] and Payment.objects.get(pk=p.pk).account is None  # the desk's payment still went through
    drawer.refresh_from_db()
    assert not drawer.is_active and services.balance_of(drawer) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_deactivating_a_drawer_while_a_payment_lands_in_it_is_refused():
    w = World("race")
    drawer = cash(w, w.a)
    m = w.new_member("Ravi", "9811111111", w.a)
    sell(m, w.monthly, by=w.desk)
    p, deactivated = _overlap(lambda: take_payment(m, 1_500_00, "cash", by=w.desk), lambda: services.deactivate(drawer))
    assert deactivated == "not_empty" and Payment.objects.get(pk=p.pk).account == drawer
    drawer.refresh_from_db()
    assert drawer.is_active and services.balance_of(drawer) == 1_500_00


def test_an_account_is_deactivated_only_once_empty(w):
    hdfc, other_bank = bank(w, branches=[w.a, w.b], opening=1_000_00), bank(w, name="ICICI", number="000401234567", opening=0)
    c = w.client(w.admin)
    r = c.post(f"{ACCOUNTS}{hdfc.id}/deactivate/")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "not_empty")
    c.post(MOVES, {"kind": "transfer", "from_account": hdfc.id, "to_account": other_bank.id, "amount_paise": 1_000_00}, format="json")
    r = c.post(f"{ACCOUNTS}{hdfc.id}/deactivate/")
    assert r.status_code == 200 and r.json()["is_active"] is False and r.json()["branches"] == []
    assert paid(w, "Ravi", "9811111111", "upi").account is None  # A has no bank account now
    assert c.patch(f"{ACCOUNTS}{hdfc.id}/", {"branches": [w.a.id]}, format="json").json()["error"]["code"] == "inactive"
    assert c.post(f"{ACCOUNTS}{hdfc.id}/deactivate/").json()["error"]["code"] == "inactive"
    assert c.post(f"{ACCOUNTS}{hdfc.id}/activate/").json()["is_active"] is True
    assert [a.action for a in AuditLog.objects.filter(object_type="Account", object_id=str(hdfc.id)).order_by("at", "id")][-2:] == ["account.deactivated", "account.activated"]
    assert Account.objects.filter(id=hdfc.id).exists()  # never deleted


def test_only_admins_reach_money(w):
    hdfc = bank(w, branches=[w.a])
    for who in (w.desk, w.trainer):
        c = w.client(who)
        assert c.get(ACCOUNTS).status_code == 403
        assert c.get(f"{ACCOUNTS}overview/").status_code == 403
        assert c.get(MOVES).status_code == 403
        assert c.post(MOVES, {"kind": "deposit", "to_account": hdfc.id, "amount_paise": 100}, format="json").status_code == 403
        assert c.post(f"{ACCOUNTS}branch/", {"branch": w.a.id, "account": None}, format="json").status_code == 403
    assert w.member_client().get(ACCOUNTS).status_code == 403
    assert BranchAccount.objects.filter(branch=w.a).exists() and not MoneyMove.objects.exists()


def test_another_gyms_accounts_stay_out_of_reach(w, other):
    mine, theirs = bank(w, branches=[w.a]), bank(other, branches=[other.a])
    c = w.client(w.admin)
    assert c.get(f"{ACCOUNTS}{theirs.id}/").status_code == 404
    assert [a["id"] for a in c.get(ACCOUNTS).json()] == [mine.id]
    assert c.post(MOVES, {"kind": "deposit", "to_account": theirs.id, "amount_paise": 100}, format="json").status_code == 400
    assert c.post(MOVES, {"kind": "transfer", "from_account": mine.id, "to_account": theirs.id, "amount_paise": 100}, format="json").status_code == 400
    assert c.post(f"{ACCOUNTS}branch/", {"branch": other.a.id, "account": mine.id}, format="json").status_code == 400
    assert c.post(ACCOUNTS, {"kind": "cash", "branch": other.a.id}, format="json").status_code == 400
    assert c.patch(f"{ACCOUNTS}{mine.id}/", {"branches": [other.b.id]}, format="json").status_code == 400
    # The same account number in another gym is that gym's business.
    assert c.post(ACCOUNTS, {"kind": "bank", "name": "Copy", "bank_name": "HDFC", "account_number": theirs.account_number}, format="json").status_code == 400  # mine has it
    assert other.client(other.admin).get(f"{ACCOUNTS}overview/").json()["totals"]["bank_paise"] == 1_00_000_00


def test_money_reads_stay_within_a_query_budget(w, django_assert_max_num_queries):
    def grow(n):
        for i in range(n):
            a = bank(w, name=f"Bank {Account.objects.count()}", number=f"9000000{Account.objects.count():05d}", branches=[])
            MoneyMove.objects.create(gym=w.gym, kind="deposit", to_account=a, amount_paise=100, moved_on=w.today, created_by=w.admin)
    cash(w, w.a)
    bank(w, branches=[w.a, w.b])
    grow(2)
    c = w.client(w.admin)
    urls = [ACCOUNTS, f"{ACCOUNTS}overview/", MOVES]
    few = {}
    for url in urls:
        with django_assert_max_num_queries(10) as q:
            assert c.get(url).status_code == 200
        few[url] = len(q.captured_queries)
    grow(8)
    for url in urls:
        with django_assert_max_num_queries(few[url]):
            assert c.get(url).status_code == 200


def test_money_dated_before_an_account_was_added_stays_out_of_it(w):
    """The opening balance is what the account held the day it was added, so anything dated earlier is in it already."""
    hdfc, drawer = bank(w, branches=[w.a]), cash(w, w.a, opening=5_000_00)
    c = w.client(w.admin)
    yesterday, today = (w.today - timedelta(days=1)).isoformat(), w.today.isoformat()
    r = c.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 30000, "method": "cash", "spent_on": yesterday}, format="json")
    assert Expense.objects.get(id=r.json()["id"]).account is None
    assert c.patch(f"/api/expenses/{r.json()['id']}/", {"spent_on": today}, format="json").status_code == 200  # was today after all
    assert Expense.objects.get(id=r.json()["id"]).account == drawer
    assert c.patch(f"/api/expenses/{r.json()['id']}/", {"spent_on": yesterday}, format="json").status_code == 200
    assert Expense.objects.get(id=r.json()["id"]).account is None
    # A payment taken before the drawer was counted, corrected to cash later, was in that count.
    p = paid(w, "Ravi", "9811111111", "upi")
    Payment.objects.filter(pk=p.pk).update(taken_at=p.taken_at - timedelta(days=2))
    assert c.patch(f"/api/payments/{p.id}/", {"method": "cash", "reason": "Paid in cash"}, format="json").status_code == 200
    p.refresh_from_db()
    assert p.account is None
    r = c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 100, "moved_on": yesterday}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "before_opened")
    assert balances(c) == {"HDFC current": 1_00_000_00, "A cash": 5_000_00}


def test_a_deactivated_account_stays_in_the_totals_and_out_of_voids(w):
    hdfc, drawer = bank(w, branches=[w.a], opening=0), cash(w, w.a, opening=0)
    c = w.client(w.admin)
    p = paid(w, "Ravi", "9811111111", "cash", paise=1_500_00)
    banked = c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 1_500_00}, format="json").json()
    assert c.post(f"{ACCOUNTS}{drawer.id}/deactivate/").status_code == 200
    # Undoing the banking would put ₹1,500 back into a drawer no one counts any more.
    r = c.post(f"{MOVES}{banked['id']}/void/", {"reason": "Wrong"}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "inactive")
    # A payment voided after its drawer was closed still leaves the gym's money: the totals say so.
    c.post(f"/api/payments/{p.id}/void/", {"reason": "Cheque bounced"}, format="json")
    totals = c.get(f"{ACCOUNTS}overview/").json()["totals"]
    assert totals == {"cash_paise": -1_500_00, "bank_paise": 1_500_00, "total_paise": 0}


def test_a_move_into_an_account_deactivated_meanwhile_is_refused(w):
    drawer = cash(w, w.a, opening=0)
    stale = Account.objects.get(pk=drawer.pk)  # read before someone else deactivated it
    services.deactivate(drawer)
    with pytest.raises(RuleBroken) as e:
        services.move(w.gym, kind="deposit", to_account=stale, amount_paise=100, moved_on=w.today, by=w.admin)
    assert e.value.rule_code == "inactive" and not MoneyMove.objects.exists()


def test_a_statement_lists_the_month_with_a_running_balance(w):
    hdfc, drawer = bank(w, branches=[w.a], opening=0), cash(w, w.a, opening=1_000_00)
    c = w.client(w.admin)
    paid(w, "Ravi", "9811111111", "cash", paise=1_400_00)
    gone = paid(w, "Sita", "9811111112", "cash", paise=700_00)
    c.post(f"/api/payments/{gone.id}/void/", {"reason": "Duplicate"}, format="json")
    c.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 300_00, "method": "cash", "paid_to": "Water cans", "spent_on": w.today.isoformat()}, format="json")
    c.post(MOVES, {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 1_500_00, "note": "Banked"}, format="json")
    r = c.get(f"{ACCOUNTS}{drawer.id}/statement/")
    assert r.status_code == 200, r.json()
    s = r.json()
    assert (s["from"], s["to"], s["opening_paise"]) == (w.today.isoformat(), w.today.isoformat(), 1_000_00)
    assert [(e["kind"], e["title"], e["amount_paise"], e["balance_paise"]) for e in s["entries"]] == [
        ("payment", "Ravi", 1_400_00, 2_400_00), ("expense", "Water cans", -300_00, 2_100_00), ("move", "To HDFC current", -1_500_00, 600_00)]
    assert (s["in_paise"], s["out_paise"], s["closing_paise"]) == (1_400_00, 1_800_00, services.balance_of(drawer))
    into = c.get(f"{ACCOUNTS}{hdfc.id}/statement/", {"month": w.today.strftime("%Y-%m")}).json()
    assert [(e["title"], e["amount_paise"]) for e in into["entries"]] == [("From A cash", 1_500_00)]
    # A month before the account was added shows nothing moving, from the opening balance.
    before = c.get(f"{ACCOUNTS}{drawer.id}/statement/", {"month": (w.today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")}).json()
    assert (before["entries"], before["opening_paise"], before["closing_paise"]) == ([], 1_000_00, 1_000_00)
    assert c.get(f"{ACCOUNTS}{drawer.id}/statement/", {"month": "2026-13"}).status_code == 400
    assert w.client(w.desk).get(f"{ACCOUNTS}{drawer.id}/statement/").status_code == 403


def test_a_statement_from_another_gym_is_not_found(w, other):
    theirs = cash(other, other.a)
    assert w.client(w.admin).get(f"{ACCOUNTS}{theirs.id}/statement/").status_code == 404


def test_lowering_an_opening_balance_cant_leave_the_account_below_zero(w):
    drawer = cash(w, w.a, opening=1_000_00)
    c = w.client(w.admin)
    c.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 700_00, "method": "cash", "spent_on": w.today.isoformat()}, format="json")
    r = c.patch(f"{ACCOUNTS}{drawer.id}/", {"opening_balance_paise": 500_00}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "below_zero")
    assert r.json()["error"]["message"] == "That would leave A cash at −₹200. Enter ₹700 or more."
    drawer.refresh_from_db()
    assert drawer.opening_balance_paise == 1_000_00 and not AuditLog.objects.filter(action="account.changed").exists()
    r = c.patch(f"{ACCOUNTS}{drawer.id}/", {"opening_balance_paise": 700_00}, format="json")
    assert (r.status_code, r.json()["balance_paise"]) == (200, 0)
    log = AuditLog.objects.get(action="account.changed")
    assert (log.before["opening_balance_paise"], log.after["opening_balance_paise"]) == (1_000_00, 700_00)
    # Already below zero from the desk's expenses: raising it is still allowed, even when it stays below.
    c.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 500_00, "method": "cash", "spent_on": w.today.isoformat()}, format="json")
    assert c.patch(f"{ACCOUNTS}{drawer.id}/", {"opening_balance_paise": 800_00}, format="json").json()["balance_paise"] == -400_00
