"""Dumbelo invoices: the billing-day job, what goes on an invoice, numbers, payments, voids and who can see them."""
import importlib
from datetime import date, timedelta

import pytest
from django.apps import apps as django_apps
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.billing import invoicing, services
from apps.billing.models import BranchRequest, GymBilling, Invoice, InvoiceLine, InvoicePayment, financial_year
from apps.billing.tasks import write_due
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.gyms.models import Gym
from tests.conftest import PRICES, World
from tests.test_billing import _overlap, dumbelo

INVOICES = "/api/billing/invoices/"
CONSOLE = "/api/platform/invoices/"
CHARGES = "/api/platform/charges/"
MONTH = PRICES["base_paise"] + 2 * PRICES["per_branch_paise"]  # the World's plan: room for 2 branches


def write(w, starts=date(2026, 11, 1)) -> Invoice:
    inv = invoicing.write_invoice(w.gym, starts)
    assert inv is not None
    return inv


def approve(w, count=1):
    req = services.ask_for_branches(w.gym, count=count, note="", by=w.admin.user)
    approver = User.objects.get_or_create(email="approver@dumbelo.com", defaults={"name": "Approver", "is_superuser": True})[0]
    return services.approve(req, by=approver)


def pay(c, inv, amount, **extra):
    body = {"amount_paise": amount, "method": "bank", "paid_on": timezone.localdate().isoformat(), "reference": "UTR123", **extra}
    return c.post(f"{CONSOLE}{inv.id}/payments/", body, format="json")


# Writing an invoice

def test_an_invoice_bills_the_month_ahead_at_the_quota(w):
    inv = write(w)
    assert (inv.period_from, inv.period_to, inv.issued_on, inv.due_on) == (date(2026, 11, 1), date(2026, 11, 30), date(2026, 11, 1), date(2026, 11, 8))
    assert inv.number == "RL/2026-27/0001" and inv.status == Invoice.OPEN
    assert (inv.subtotal_paise, inv.tax_paise, inv.total_paise) == (MONTH, 0, MONTH)
    lines = list(inv.lines.values_list("kind", "description", "quantity", "rate_paise", "amount_paise", "tax_paise"))
    assert lines == [
        ("base", "Dumbelo plan, 1 Nov to 30 Nov", 1, PRICES["base_paise"], PRICES["base_paise"], 0),
        ("branches", "2 branches, 1 Nov to 30 Nov", 2, PRICES["per_branch_paise"], 2 * PRICES["per_branch_paise"], 0),
    ]


def test_writing_the_same_month_again_writes_nothing(w):
    first = write(w)
    assert invoicing.write_invoice(w.gym, date(2026, 11, 1)) is None
    first.status = Invoice.VOID
    first.save()
    assert invoicing.write_invoice(w.gym, date(2026, 11, 1)) is None  # a voided month isn't rewritten by itself
    assert Invoice.objects.filter(gym=w.gym).count() == 1


@pytest.mark.parametrize("billing_day, starts, ends", [
    (1, date(2027, 2, 1), date(2027, 2, 28)),
    (1, date(2028, 2, 1), date(2028, 2, 29)),    # a leap year
    (28, date(2027, 1, 28), date(2027, 2, 27)),
    (28, date(2027, 2, 28), date(2027, 3, 27)),
    (15, date(2026, 12, 15), date(2027, 1, 14)),  # across the new year
    (10, date(2026, 10, 10), date(2026, 11, 9)),
])
def test_a_billing_month_runs_to_the_day_before_the_next_billing_day(w, billing_day, starts, ends):
    GymBilling.objects.filter(gym=w.gym).update(billing_day=billing_day)
    inv = write(w, starts)
    assert (inv.period_from, inv.period_to) == (starts, ends)
    assert services.billing_month(billing_day, starts) == (starts, ends)


def test_numbers_run_in_one_series_per_financial_year(w, other):
    march = write(w, date(2027, 3, 1))
    april = write(w, date(2027, 4, 1))
    theirs = write(other, date(2027, 3, 1))
    may = write(w, date(2027, 5, 1))
    assert (march.number, theirs.number) == ("RL/2026-27/0001", "RL/2026-27/0002")  # every gym shares the series
    assert (april.number, may.number) == ("RL/2027-28/0001", "RL/2027-28/0002")  # April starts it again
    invoicing.void_invoice(may, reason="Wrong month", by=w.admin.user)
    assert write(w, date(2027, 6, 1)).number == "RL/2027-28/0003"  # a voided number is never given again
    assert financial_year(date(2027, 3, 31)) == "2026-27" and financial_year(date(2027, 4, 1)) == "2027-28"


def test_pending_charges_and_branches_added_last_month_go_on_the_next_invoice(w):
    req = approve(w)  # today, in some billing month before November's invoice
    setup = invoicing.add_charge(w.gym, kind=InvoiceLine.WHATSAPP_SETUP, by=w.admin.user)
    inv = write(w, date(2027, 1, 1))
    kinds = list(inv.lines.values_list("kind", "quantity", "amount_paise"))
    assert ("branches", 3, 3 * PRICES["per_branch_paise"]) in kinds  # the new quota, for the month ahead
    assert ("branches_pro_rata", 1, req.pro_rata_paise) in kinds and ("whatsapp_setup", 1, PRICES["whatsapp_setup_paise"]) in kinds
    assert inv.total_paise == PRICES["base_paise"] + 3 * PRICES["per_branch_paise"] + req.pro_rata_paise + PRICES["whatsapp_setup_paise"]
    setup.refresh_from_db()
    assert setup.invoice == inv and not InvoiceLine.objects.filter(gym=w.gym, invoice=None).exists()
    assert write(w, date(2027, 2, 1)).total_paise == PRICES["base_paise"] + 3 * PRICES["per_branch_paise"]  # billed once


def test_a_branch_approved_on_the_billing_day_before_the_invoice_is_billed_once(w):
    starts = date(2026, 11, 1)
    req = services.ask_for_branches(w.gym, count=1, note="", by=w.admin.user)
    req.status = BranchRequest.APPROVED
    cost = services.pro_rata(PRICES["per_branch_paise"], 1, 1, starts)  # all of November: approved on the 1st
    req.charged_from, req.charged_to, req.period_days, req.rate_paise, req.pro_rata_paise = cost.charged_from, cost.charged_to, cost.period_days, cost.rate_paise, cost.amount_paise
    req.save()
    services.pro_rata_line(req)
    GymBilling.objects.filter(gym=w.gym).update(branch_quota=3)
    inv = write(w, starts)
    lines = dict(inv.lines.values_list("kind", "quantity"))
    assert lines["branches"] == 2 and lines["branches_pro_rata"] == 1
    assert inv.total_paise == PRICES["base_paise"] + 3 * PRICES["per_branch_paise"]


def test_a_plan_at_nothing_is_paid_as_it_is_written(w):
    GymBilling.objects.filter(gym=w.gym).update(base_paise=0, per_branch_paise=0)
    inv = write(w)
    assert inv.total_paise == 0 and inv.status == Invoice.PAID
    assert GymBilling.objects.get(gym=w.gym).paid_until == date(2026, 11, 30)


def test_the_whatsapp_usage_hook_bills_nothing_until_messages_are_counted(w):
    assert invoicing.whatsapp_usage_lines(w.billing, date(2026, 11, 1)) == []


# The billing-day job

def test_the_job_bills_active_gyms_on_their_billing_day_and_is_safe_to_repeat(w, other):
    GymBilling.objects.filter(gym=other.gym).update(billing_day=15)
    trial = World("trial", n=3)
    Gym.objects.filter(pk=trial.gym.pk).update(status=Gym.TRIAL)
    paused = World("paused", n=4)
    Gym.objects.filter(pk=paused.gym.pk).update(status=Gym.SUSPENDED)
    assert write_due(date(2026, 11, 1)) == 1
    assert write_due(date(2026, 11, 1)) == 0
    assert list(Invoice.objects.values_list("gym", flat=True)) == [w.gym.id]
    assert write_due(date(2026, 11, 15)) == 1 and Invoice.objects.get(gym=other.gym).period_from == date(2026, 11, 15)
    assert write_due(date(2026, 11, 2)) == 0
    written = AuditLog.objects.filter(action="invoice.written")
    assert written.count() == 2 and written.filter(gym=w.gym, actor=None).exists()


def test_the_job_follows_each_gyms_own_day(w):
    today = clock.today(w.gym)
    GymBilling.objects.filter(gym=w.gym).update(billing_day=min(today.day, 28))
    assert write_due() == (1 if today.day <= 28 else 0)
    assert write_due() == 0


def test_one_gyms_failure_never_stops_the_rest(w, other, monkeypatch):
    real = invoicing.write_invoice

    def flaky(gym, on):
        if gym.pk == w.gym.pk:
            raise RuntimeError("database hiccup")
        return real(gym, on)

    monkeypatch.setattr(invoicing, "write_invoice", flaky)
    assert write_due(date(2026, 11, 1)) == 1
    assert Invoice.objects.get().gym == other.gym


def test_the_command_writes_a_missed_billing_day(w, capsys):
    call_command("write_invoices", "--day", "2026-11-01")
    assert "1 invoice written." in capsys.readouterr().out
    call_command("write_invoices", "--day", "2026-11-01")
    assert "0 invoices written." in capsys.readouterr().out


# Payments

def test_part_payments_never_more_than_owed_and_paid_in_full_moves_paid_until(w):
    inv = write(w)
    c = dumbelo()
    r = pay(c, inv, 5_000_00)
    assert r.status_code == 200, r.content
    body = r.json()
    year = financial_year(timezone.localdate())
    assert body["paid_paise"] == 5_000_00 and body["owed_paise"] == MONTH - 5_000_00 and body["status"] == "open"
    assert body["payments"][0]["receipt_number"] == f"RLR/{year}/0001" and body["payments"][0]["recorded_by_name"] == "Dumbelo Ops"
    too_much = pay(c, inv, MONTH)
    assert too_much.status_code == 409 and too_much.json()["error"] == {"code": "overpaid", "message": f"RL/2026-27/0001 owes ₹2,199. Record that or less."}
    assert pay(c, inv, MONTH - 5_000_00).json()["status"] == "paid"
    assert pay(c, inv, 1).json()["error"]["code"] == "nothing_owed"
    assert GymBilling.objects.get(gym=w.gym).paid_until == date(2026, 11, 30)
    assert AuditLog.objects.filter(gym=w.gym, action="invoice.payment_recorded").count() == 2


@pytest.mark.parametrize("body, field", [
    ({"amount_paise": 0}, "amount_paise"), ({"method": "bitcoin"}, "method"), ({"paid_on": "soon"}, "paid_on"),
])
def test_payments_are_checked(w, body, field):
    r = pay(dumbelo(), write(w), 100_00, **body)
    assert r.status_code == 400 and field in r.json()["error"]["fields"]


def test_a_payment_dated_in_the_future_is_refused(w):
    tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
    assert pay(dumbelo(), write(w), 100_00, paid_on=tomorrow).json()["error"]["code"] == "future_date"


def test_voids_keep_history(w):
    inv = write(w)
    c = dumbelo()
    paid = pay(c, inv, MONTH).json()["payments"][0]
    assert c.post(f"{CONSOLE}{inv.id}/void/", {"reason": "Wrong prices"}, format="json").json()["error"]["code"] == "has_payments"
    assert c.post(f"/api/platform/invoice-payments/{paid['id']}/void/", {"reason": ""}, format="json").status_code == 400
    r = c.post(f"/api/platform/invoice-payments/{paid['id']}/void/", {"reason": "The transfer bounced"}, format="json")
    assert r.status_code == 200 and r.json()["voided"] and r.json()["voided_by_name"] == "Dumbelo Ops"
    assert c.post(f"/api/platform/invoice-payments/{paid['id']}/void/", {"reason": "again"}, format="json").json()["error"]["code"] == "already_void"
    after = c.get(f"{CONSOLE}{inv.id}/").json()
    assert after["status"] == "open" and after["owed_paise"] == MONTH and len(after["payments"]) == 1  # still there, voided
    assert GymBilling.objects.get(gym=w.gym).paid_until is None

    r = c.post(f"{CONSOLE}{inv.id}/void/", {"reason": "Wrong prices"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "void" and r.json()["void_reason"] == "Wrong prices"
    assert len(r.json()["lines"]) == 2 and r.json()["number"] == "RL/2026-27/0001" and r.json()["owed_paise"] == 0
    assert pay(c, inv, 100_00).json()["error"]["code"] == "invoice_void"
    assert c.post(f"{CONSOLE}{inv.id}/void/", {"reason": "again"}, format="json").json()["error"]["code"] == "already_void"
    assert Invoice.objects.filter(pk=inv.pk).exists() and InvoicePayment.objects.filter(pk=paid["id"]).exists()
    actions = set(AuditLog.objects.filter(gym=w.gym).values_list("action", flat=True))
    assert {"invoice.payment_recorded", "invoice.payment_voided", "invoice.voided"} <= actions


def test_voiding_a_payment_on_a_paid_invoice_moves_paid_until_back(w):
    october = write(w, date(2026, 10, 1))
    november = write(w, date(2026, 11, 1))
    c = dumbelo()
    pay(c, october, MONTH)
    last = pay(c, november, MONTH).json()["payments"][0]
    assert GymBilling.objects.get(gym=w.gym).paid_until == date(2026, 11, 30)
    c.post(f"/api/platform/invoice-payments/{last['id']}/void/", {"reason": "Bounced"}, format="json")
    assert GymBilling.objects.get(gym=w.gym).paid_until == date(2026, 10, 31)


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_two_payments_at_once_never_pay_more_than_owed():
    w = World("race")
    inv = write(w)
    by = w.admin.user
    today = timezone.localdate()

    def paying():
        return invoicing.record_payment(inv, amount_paise=MONTH - 1_000_00, method="bank", paid_on=today, by=by).receipt_number

    first, second = _overlap(paying, paying)
    assert first.startswith("RLR/") and second == "overpaid"
    assert Invoice.objects.with_paid().get(pk=inv.pk).paid_paise() == MONTH - 1_000_00


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="SQLite has no row locks to race over")
def test_two_invoices_written_at_once_never_share_a_number():
    a, b = World("race-a"), World("race-b", n=1)
    first, second = _overlap(lambda: write(a).number, lambda: write(b).number)
    assert {first, second} == {"RL/2026-27/0001", "RL/2026-27/0002"}


# Charges added by hand

def test_add_charge_takes_the_gyms_prices_and_waits_for_the_next_invoice(w):
    c = dumbelo()
    r = c.post(CHARGES, {"gym": w.gym.id, "kind": "machine_setup", "quantity": 2}, format="json")
    assert r.status_code == 201, r.content
    assert (r.json()["description"], r.json()["amount_paise"], r.json()["added_by_name"]) == ("Attendance machine setup, 2 machines", 2 * PRICES["machine_setup_paise"], "Dumbelo Ops")
    assert c.post(CHARGES, {"gym": w.gym.id, "kind": "whatsapp_setup"}, format="json").json()["amount_paise"] == PRICES["whatsapp_setup_paise"]
    other = c.post(CHARGES, {"gym": w.gym.id, "kind": "adjustment", "rate_paise": 500_00, "description": "Extra training day"}, format="json")
    assert other.json()["kind"] == "adjustment" and other.json()["amount_paise"] == 500_00
    assert c.get(CHARGES, {"gym": w.gym.id}).json()["count"] == 3
    assert AuditLog.objects.filter(gym=w.gym, action="charge.added").count() == 3


def test_another_charge_needs_its_amount_and_what_it_is_for(w):
    r = dumbelo().post(CHARGES, {"gym": w.gym.id, "kind": "adjustment"}, format="json")
    assert r.status_code == 400 and set(r.json()["error"]["fields"]) == {"rate_paise", "description"}
    assert dumbelo("b@dumbelo.com").post(CHARGES, {"gym": w.gym.id, "kind": "base", "rate_paise": 1}, format="json").status_code == 400


def test_a_charge_can_be_taken_back_until_it_is_billed(w):
    c = dumbelo()
    charge = c.post(CHARGES, {"gym": w.gym.id, "kind": "whatsapp_setup"}, format="json").json()
    assert c.delete(f"{CHARGES}{charge['id']}/").status_code == 204
    assert AuditLog.objects.get(gym=w.gym, action="charge.removed").before["kind"] == "whatsapp_setup"
    billed = c.post(CHARGES, {"gym": w.gym.id, "kind": "whatsapp_setup"}, format="json").json()
    write(w)
    assert c.delete(f"{CHARGES}{billed['id']}/").status_code == 404  # billed: no longer a pending charge
    with pytest.raises(RuleBroken) as e:
        invoicing.remove_charge(InvoiceLine.objects.get(pk=billed["id"]))
    assert e.value.rule_code == "billed"
    pro_rata = approve(w).invoice_line
    assert c.delete(f"{CHARGES}{pro_rata.id}/").json()["error"]["code"] == "not_a_charge"


# Who sees what

def test_a_suspended_gyms_admins_read_their_invoices_and_receipts(w):
    inv = write(w)
    pay(dumbelo(), inv, 1_000_00)
    Gym.objects.filter(pk=w.gym.pk).update(status=Gym.SUSPENDED)
    admin = w.client(w.admin)
    rows = admin.get(INVOICES).json()
    assert rows["count"] == 1 and rows["results"][0]["owed_paise"] == MONTH - 1_000_00
    detail = admin.get(f"{INVOICES}{inv.id}/").json()
    assert detail["gym_name"] == w.gym.name and len(detail["lines"]) == 2
    assert detail["payments"][0]["receipt_number"].startswith("RLR/") and "recorded_by_name" not in detail["payments"][0]
    assert admin.get("/api/billing/plan/").json()["owed_paise"] == MONTH - 1_000_00


def test_desks_trainers_and_members_cant_see_invoices(w):
    inv = write(w)
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(INVOICES).status_code == 403
        assert c.get(f"{INVOICES}{inv.id}/").status_code == 403


def test_another_gyms_invoice_is_not_found(w, other):
    theirs = write(other)
    assert w.client(w.admin).get(f"{INVOICES}{theirs.id}/").status_code == 404
    assert w.client(w.admin).get(INVOICES).json()["count"] == 0


def test_only_dumbelo_admins_reach_invoices_in_the_console(w):
    inv = write(w)
    support = APIClient()
    support.force_authenticate(User.objects.create_user(email="support@dumbelo.com", password="pass12345", name="Support", is_staff=True))
    for c in (w.client(w.admin), support):
        assert c.get(CONSOLE).status_code == 403
        assert pay(c, inv, 100_00).status_code == 403
        assert c.post(CHARGES, {"gym": w.gym.id, "kind": "whatsapp_setup"}, format="json").status_code == 403


def test_invoice_lists_keep_a_query_budget(w, other, django_assert_max_num_queries):
    c = dumbelo()
    for month in range(1, 6):
        inv = write(w, date(2027, month, 1))
        pay(c, inv, 1_000_00)
        write(other, date(2027, month, 1))
    with django_assert_max_num_queries(3):
        rows = c.get(CONSOLE).json()
    assert rows["count"] == 10 and all(r["gym_name"] for r in rows["results"])
    assert c.get(CONSOLE, {"gym": w.gym.id, "status": "open"}).json()["count"] == 5
    admin = w.client(w.admin)
    with django_assert_max_num_queries(6):  # sign-in, gym, role and the page
        mine = admin.get(INVOICES).json()
    assert mine["count"] == 5 and mine["results"][0]["paid_paise"] == 1_000_00
    assert [r["period_from"] for r in mine["results"]][:2] == ["2027-05-01", "2027-04-01"]  # newest first
    with django_assert_max_num_queries(7):
        admin.get(f"{INVOICES}{inv.id}/")


def test_the_gyms_list_shows_what_every_gym_owes(w, other, django_assert_max_num_queries):
    c = dumbelo()
    paid = write(w, date(2026, 10, 1))
    pay(c, paid, MONTH)
    pay(c, write(w, date(2026, 11, 1)), 1_000_00)
    void = write(other)
    invoicing.void_invoice(void, reason="Trial month", by=w.admin.user)
    with django_assert_max_num_queries(3):
        rows = {g["id"]: g["owed_paise"] for g in c.get("/api/platform/gyms/").json()["results"]}
    assert rows == {w.gym.id: MONTH - 1_000_00, other.gym.id: 0}
    assert c.get(f"/api/platform/gyms/{w.gym.id}/plan/").json()["owed_paise"] == MONTH - 1_000_00


# Requests approved before invoices existed

def test_requests_approved_before_invoices_get_their_pending_line(w):
    req = approve(w)
    made_now = req.invoice_line.description
    req.invoice_line.delete()
    migration = importlib.import_module("apps.billing.migrations.0004_pending_lines_for_approved_requests")
    migration.lines_for_approved(django_apps, None)
    line = InvoiceLine.objects.get(branch_request=req)
    assert line.invoice is None and line.amount_paise == req.pro_rata_paise and line.kind == "branches_pro_rata"
    assert line.description == made_now and made_now.startswith("1 branch added, ")
    migration.lines_for_approved(django_apps, None)
    assert InvoiceLine.objects.filter(branch_request=req).count() == 1
