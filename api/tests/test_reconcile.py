"""Checking a bank account against the bank's statement: ticks, reconciling up to a day, and the lock that follows."""
from datetime import timedelta

from apps.audit.models import AuditLog
from apps.finance.models import Account, StatementTick
from tests.test_finance import ACCOUNTS, MOVES, bank, cash, paid


def setup(w):
    """HDFC used by branch A, opened with ₹10,000: a UPI payment of ₹1,500 in, a bank expense of ₹400 out, ₹1,000 to ICICI."""
    hdfc = bank(w, branches=[w.a], opening=10_000_00)
    icici = bank(w, name="ICICI", number="000401234567", opening=0)
    c = w.client(w.admin)
    p = paid(w, "Ravi", "9811111111", "upi", paise=1_500_00)
    e = c.post("/api/expenses/", {"branch": w.a.id, "category": "utilities", "amount_paise": 400_00, "method": "bank", "spent_on": w.today.isoformat()},
               format="json").json()
    m = c.post(MOVES, {"kind": "transfer", "from_account": hdfc.id, "to_account": icici.id, "amount_paise": 1_000_00}, format="json").json()
    return hdfc, icici, c, p, e, m


def tick(c, account, entries, ticked=True):
    return c.post(f"{ACCOUNTS}{account.id}/tick/", {"entries": [{"kind": k, "id": i} for k, i in entries], "ticked": ticked}, format="json")


def marks(c, account):
    return {(e["kind"], e["id"]): (e["ticked"], e["reconciled"]) for e in c.get(f"{ACCOUNTS}{account.id}/statement/").json()["entries"]}


def test_ticked_entries_reconcile_when_they_match_the_bank(w):
    hdfc, _, c, p, e, m = setup(w)
    assert tick(c, hdfc, [("payment", p.id), ("expense", e["id"])]).status_code == 204
    s = c.get(f"{ACCOUNTS}{hdfc.id}/statement/").json()
    assert (s["cleared_paise"], s["reconciled"]) == (11_100_00, None)  # the transfer isn't on the bank's statement yet
    assert marks(c, hdfc) == {("payment", p.id): (True, False), ("expense", e["id"]): (True, False), ("move", m["id"]): (False, False)}
    r = c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": w.today.isoformat(), "bank_balance_paise": 10_100_00}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "not_matched")
    assert "come to ₹11,100, ₹1,000 more than the bank's" in r.json()["error"]["message"]
    tick(c, hdfc, [("move", m["id"])])
    r = c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": w.today.isoformat(), "bank_balance_paise": 10_100_00}, format="json")
    assert r.status_code == 200, r.json()
    assert (r.json()["up_to"], r.json()["bank_balance_paise"]) == (w.today.isoformat(), 10_100_00)
    assert set(marks(c, hdfc).values()) == {(True, True)}
    assert c.get(f"{ACCOUNTS}{hdfc.id}/statement/").json()["reconciled"]["by_name"] == w.admin.user.name
    assert AuditLog.objects.get(action="account.reconciled").after == {"up_to": w.today.isoformat(), "bank_balance_paise": 10_100_00, "entries": 3}


def test_reconciled_entries_cant_change_until_an_admin_unreconciles_them(w):
    hdfc, icici, c, p, e, m = setup(w)
    tick(c, hdfc, [("payment", p.id), ("expense", e["id"]), ("move", m["id"])])
    c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": w.today.isoformat(), "bank_balance_paise": 10_100_00}, format="json")
    refused = [
        c.patch(f"/api/payments/{p.id}/", {"amount_paise": 1_000_00, "reason": "Typo"}, format="json"),
        c.post(f"/api/payments/{p.id}/void/", {"reason": "Bounced"}, format="json"),
        c.patch(f"/api/expenses/{e['id']}/", {"method": "cash"}, format="json"),
        c.delete(f"/api/expenses/{e['id']}/"),
        c.post(f"{MOVES}{m['id']}/void/", {"reason": "Wrong"}, format="json"),
        tick(c, hdfc, [("payment", p.id)], ticked=False),
    ]
    assert [(r.status_code, r.json()["error"]["code"]) for r in refused] == [(409, "reconciled")] * 6
    assert c.patch(f"/api/payments/{p.id}/", {"note": "UPI ref 1234", "reason": "Added the reference"}, format="json").status_code == 200
    assert c.patch(f"/api/expenses/{e['id']}/", {"paid_to": "BESCOM"}, format="json").status_code == 200
    # The transfer is reconciled on HDFC's side only: ICICI's statement hasn't ticked it.
    assert marks(c, icici) == {("move", m["id"]): (False, False)}
    r = c.post(f"{ACCOUNTS}{hdfc.id}/unreconcile/", {"kind": "payment", "id": p.id, "reason": "The cheque bounced"}, format="json")
    assert r.status_code == 204
    log = AuditLog.objects.get(action="account.unreconciled")
    assert (log.after["entry"], log.after["reason"]) == (p.id, "The cheque bounced")
    assert c.post(f"/api/payments/{p.id}/void/", {"reason": "Bounced"}, format="json").status_code == 200
    assert not StatementTick.objects.filter(kind="payment", entry_id=p.id).exists()  # a voided payment isn't on any statement
    r = c.post(f"{ACCOUNTS}{hdfc.id}/unreconcile/", {"kind": "payment", "id": p.id, "reason": "Again"}, format="json")
    assert r.json()["error"]["code"] == "not_reconciled"


def test_changing_a_ticked_entry_drops_its_tick(w):
    hdfc, _, c, p, e, _ = setup(w)
    tick(c, hdfc, [("expense", e["id"])])
    assert c.patch(f"/api/expenses/{e['id']}/", {"amount_paise": 450_00}, format="json").status_code == 200
    assert marks(c, hdfc)[("expense", e["id"])] == (False, False)
    assert c.get(f"{ACCOUNTS}{hdfc.id}/statement/").json()["cleared_paise"] == 10_000_00


def test_what_can_be_ticked_and_reconciled(w):
    hdfc, _, c, p, _, _ = setup(w)
    drawer = cash(w, w.a)
    assert tick(c, drawer, [("payment", p.id)]).json()["error"]["code"] == "not_a_bank_account"
    assert tick(c, hdfc, [("payment", 999999)]).json()["error"]["code"] == "not_on_statement"
    assert tick(c, hdfc, [("salary", p.id)]).status_code == 400
    future = (w.today.replace(year=w.today.year + 1)).isoformat()
    assert c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": future, "bank_balance_paise": 0}, format="json").json()["error"]["code"] == "future"
    Account.objects.filter(pk=hdfc.pk).update(opened_on=w.today - timedelta(days=10))
    day = lambda n: (w.today - timedelta(days=n)).isoformat()  # noqa: E731
    assert c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": day(11), "bank_balance_paise": 0}, format="json").json()["error"]["code"] == "before_opened"
    assert c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": day(2), "bank_balance_paise": 10_000_00}, format="json").status_code == 200
    r = c.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": day(3), "bank_balance_paise": 10_000_00}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "before_last")


def test_only_admins_reconcile_and_only_their_own_gym(w, other):
    hdfc, _, c, p, _, _ = setup(w)
    desk = w.client(w.desk)
    assert tick(desk, hdfc, [("payment", p.id)]).status_code == 403
    assert desk.post(f"{ACCOUNTS}{hdfc.id}/reconcile/", {"up_to": w.today.isoformat(), "bank_balance_paise": 0}, format="json").status_code == 403
    theirs = bank(other, branches=[other.a])
    mine = w.client(w.admin)
    assert tick(mine, theirs, [("payment", p.id)]).status_code == 404
    assert mine.post(f"{ACCOUNTS}{theirs.id}/unreconcile/", {"kind": "payment", "id": p.id, "reason": "x"}, format="json").status_code == 404


def test_a_statement_with_ticks_stays_within_a_query_budget(w, django_assert_max_num_queries):
    hdfc, _, c, *_ = setup(w)

    def grow(n):
        for i in range(n):
            pay = paid(w, f"M{i}", f"982220{5000 + StatementTick.objects.count()}", "upi", paise=100_00)
            tick(c, hdfc, [("payment", pay.id)])
    grow(2)
    url = f"{ACCOUNTS}{hdfc.id}/statement/"
    with django_assert_max_num_queries(20) as q:
        assert c.get(url).status_code == 200
    few = len(q.captured_queries)
    grow(6)
    with django_assert_max_num_queries(few):
        assert c.get(url).status_code == 200
