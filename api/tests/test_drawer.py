"""Closing the cash drawer: the desk counts, the app shows what it should hold, an admin settles the difference."""
from datetime import timedelta

from apps.audit.models import AuditLog
from apps.finance import services
from apps.finance.models import DrawerClose, MoneyMove
from tests.test_finance import cash, paid

CLOSES = "/api/drawer-closes/"
CASH = "/api/cash/"


def count(c, branch, paise, note=""):
    return c.post(CLOSES, {"branch": branch.id, "counted_paise": paise, "note": note}, format="json")


def test_the_desk_counts_its_cash_against_what_it_should_hold(w):
    drawer = cash(w, w.a, opening=2_000_00)
    paid(w, "Ravi", "9811111111", "cash", paise=1_500_00)
    desk = w.client(w.desk)
    assert desk.get(CASH).json() == [{"branch": w.a.id, "branch_name": "A", "account": drawer.id, "balance_paise": 3_500_00, "in_paise": 1_500_00,
                                      "out_paise": 0, "close": None}]
    r = count(desk, w.a, 3_300_00, "Two notes torn")
    assert r.status_code == 201, r.json()
    c = r.json()
    assert (c["day"], c["counted_paise"], c["expected_paise"], c["difference_paise"], c["counted_by_name"], c["settled_at"]) == (
        w.today.isoformat(), 3_300_00, 3_500_00, -200_00, w.desk.user.name, None)
    assert desk.get(CASH).json()[0]["close"]["id"] == c["id"]
    # Counted again before an admin looked: the new count replaces the first, and both are in the audit log.
    again = count(desk, w.a, 3_500_00).json()
    assert again["id"] == c["id"] and again["difference_paise"] == 0 and DrawerClose.objects.count() == 1
    assert [a.action for a in AuditLog.objects.filter(object_type="DrawerClose").order_by("id")] == ["drawer.counted", "drawer.recounted"]
    assert AuditLog.objects.get(action="drawer.recounted").before["counted_paise"] == 3_300_00
    assert services.balance_of(drawer) == 3_500_00  # counting never moves the balance


def test_an_admin_settles_a_short_drawer_with_a_withdrawal(w):
    drawer = cash(w, w.a, opening=1_000_00)
    close = count(w.client(w.desk), w.a, 900_00).json()
    admin = w.client(w.admin)
    assert [x["id"] for x in admin.get(CLOSES, {"state": "to_settle"}).json()["results"]] == [close["id"]]
    r = admin.post(f"{CLOSES}{close['id']}/settle/", {"reason": "Change given twice"}, format="json")
    assert r.status_code == 200, r.json()
    s = r.json()
    assert (s["settled_by_name"], s["settle_reason"]) == (w.admin.user.name, "Change given twice") and s["settled_at"]
    m = MoneyMove.objects.get(pk=s["settle_move"])
    assert (m.kind, m.from_account, m.amount_paise, m.moved_on) == ("withdrawal", drawer, 100_00, w.today)
    assert m.note == f"Cash count, {w.today.day} {w.today.strftime('%b')}: Change given twice"
    assert services.balance_of(drawer) == 900_00 and admin.get(CLOSES, {"state": "to_settle"}).json()["results"] == []
    assert AuditLog.objects.filter(action="drawer.settled", object_id=str(close["id"])).exists()
    assert admin.post(f"{CLOSES}{close['id']}/settle/", {"reason": "Again"}, format="json").json()["error"]["code"] == "settled"
    r = count(w.client(w.desk), w.a, 950_00)
    assert (r.status_code, r.json()["error"]["code"]) == (409, "settled")


def test_extra_cash_is_settled_with_a_deposit_and_a_match_needs_nothing(w):
    drawer = cash(w, w.a, opening=1_000_00)
    admin = w.client(w.admin)
    over = count(w.client(w.desk), w.a, 1_050_00).json()
    m = MoneyMove.objects.get(pk=admin.post(f"{CLOSES}{over['id']}/settle/", {"reason": "Found in the till"}, format="json").json()["settle_move"])
    assert (m.kind, m.to_account, m.amount_paise) == ("deposit", drawer, 50_00) and services.balance_of(drawer) == 1_050_00
    cash(w, w.b, opening=500_00)
    matched = count(admin, w.b, 500_00).json()  # admins count too
    r = admin.post(f"{CLOSES}{matched['id']}/settle/", {"reason": "x"}, format="json")
    assert (r.status_code, r.json()["error"]["code"]) == (409, "nothing_to_settle")


def test_voiding_the_settling_move_opens_the_difference_again(w):
    drawer = cash(w, w.a, opening=1_000_00)
    admin = w.client(w.admin)
    close = count(w.client(w.desk), w.a, 800_00).json()
    move = admin.post(f"{CLOSES}{close['id']}/settle/", {"reason": "Short"}, format="json").json()["settle_move"]
    assert admin.post(f"/api/money-moves/{move}/void/", {"reason": "It was in the safe"}, format="json").status_code == 200
    again = admin.get(f"{CLOSES}{close['id']}/").json()
    assert (again["settled_at"], again["settle_move"], again["difference_paise"]) == (None, None, -200_00)
    assert services.balance_of(drawer) == 1_000_00
    assert count(w.client(w.desk), w.a, 1_000_00).json()["difference_paise"] == 0  # and the desk can count again


def test_the_desk_sees_its_cash_in_hand_and_todays_in_and_out_never_the_bank(w):
    from tests.test_finance import bank

    drawer = cash(w, w.a, opening=1_000_00)
    hdfc = bank(w, branches=[w.a], opening=0)
    paid(w, "Ravi", "9811111111", "cash", paise=1_500_00)
    paid(w, "Sita", "9811111112", "upi", paise=900_00)  # the bank's: not the drawer's
    admin = w.client(w.admin)
    admin.post("/api/expenses/", {"branch": w.a.id, "category": "supplies", "amount_paise": 200_00, "method": "cash", "spent_on": w.today.isoformat()}, format="json")
    admin.post("/api/money-moves/", {"kind": "transfer", "from_account": drawer.id, "to_account": hdfc.id, "amount_paise": 1_000_00}, format="json")
    row = w.client(w.desk).get(CASH).json()[0]
    assert (row["balance_paise"], row["in_paise"], row["out_paise"]) == (1_300_00, 1_500_00, 1_200_00)
    assert set(row) == {"branch", "branch_name", "account", "balance_paise", "in_paise", "out_paise", "close"}  # no bank, no revenue
    assert w.client(w.desk).get("/api/accounts/").status_code == 403  # the bank stays admin-only


def test_a_branch_without_cash_set_up_cant_be_counted(w):
    r = count(w.client(w.desk), w.a, 100_00)
    assert (r.status_code, r.json()["error"]["code"]) == (409, "no_cash_account")
    assert "Ask an admin" in r.json()["error"]["message"]
    assert w.client(w.desk).get(CASH).json() == [{"branch": w.a.id, "branch_name": "A", "account": None, "balance_paise": None, "in_paise": 0,
                                                  "out_paise": 0, "close": None}]


def test_the_desk_counts_and_sees_its_own_branches_one_day_at_a_time(w):
    cash(w, w.a)
    cash(w, w.b)
    desk, other_desk = w.client(w.desk), w.client(w.desk_b)
    b = count(other_desk, w.b, 0).json()
    r = count(desk, w.b, 0)
    assert (r.status_code, list(r.json()["error"]["fields"])) == (400, ["branch"])
    assert desk.get(CLOSES).json()["results"] == [] and desk.get(f"{CLOSES}{b['id']}/").status_code == 404
    assert [x["branch"] for x in desk.get(CASH).json()] == [w.a.id]
    assert desk.get(CASH, {"branch": w.b.id}).json() == []
    old = DrawerClose.objects.get(pk=b["id"])
    DrawerClose.objects.filter(pk=old.pk).update(day=w.today - timedelta(days=1))
    yesterday = (w.today - timedelta(days=1)).isoformat()
    assert [x["id"] for x in other_desk.get(CLOSES, {"date": yesterday}).json()["results"]] == [b["id"]]
    assert other_desk.get(CLOSES).json()["results"] == []  # today by default
    r = other_desk.get(CLOSES, {"from": yesterday, "to": w.today.isoformat()})
    assert (r.status_code, r.json()["error"]["code"]) == (409, "not_allowed")
    assert len(w.client(w.admin).get(CLOSES, {"from": yesterday}).json()["results"]) == 1
    assert desk.post(f"{CLOSES}{b['id']}/settle/", {"reason": "x"}, format="json").status_code == 403


def test_trainers_and_members_never_reach_the_drawer(w):
    cash(w, w.a)
    for c in (w.client(w.trainer), w.member_client()):
        assert c.get(CASH).status_code == 403
        assert c.get(CLOSES).status_code == 403
        assert count(c, w.a, 100).status_code == 403


def test_another_gyms_drawer_stays_out_of_reach(w, other):
    cash(other, other.a)
    theirs = count(other.client(other.desk), other.a, 0).json()
    c = w.client(w.admin)
    assert count(c, other.a, 0).status_code == 400
    assert c.get(f"{CLOSES}{theirs['id']}/").status_code == 404
    assert c.post(f"{CLOSES}{theirs['id']}/settle/", {"reason": "x"}, format="json").status_code == 404
    assert c.get(CASH, {"branch": other.a.id}).json() == []


def test_drawer_reads_stay_within_a_query_budget(w, django_assert_max_num_queries):
    from apps.gyms.models import Branch

    admin = w.client(w.admin)

    def grow(n):
        for i in range(n):
            br = Branch.objects.create(gym=w.gym, name=f"Branch {Branch.objects.count()}")
            cash(w, br)
            count(admin, br, 100)
    grow(2)
    few = {}
    for url in (CLOSES, CASH):
        with django_assert_max_num_queries(10) as q:
            assert admin.get(url).status_code == 200
        few[url] = len(q.captured_queries)
    grow(6)
    for url in (CLOSES, CASH):
        with django_assert_max_num_queries(few[url]):
            assert admin.get(url).status_code == 200
