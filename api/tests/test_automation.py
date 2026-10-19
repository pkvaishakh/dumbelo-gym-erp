"""Message switches and when messages go out: each gym's Pause and Resume, Dumbelo's times (for every gym and for
one), the receipt and task messages, and Dumbelo's own messages to a gym's owner."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import transaction

from apps.audit.models import AuditLog
from apps.billing import invoicing
from apps.billing.models import GymBilling, Invoice
from apps.billing.tasks import write_due
from apps.gyms.models import Gym
from apps.members.models import Payment
from apps.members.services import sell, take_payment
from apps.messages import notify
from apps.messages.automation import reminder_runs
from apps.messages.models import Message, NotificationRule
from apps.messages.services import send_due
from apps.messages.tasks import send_reminders
from apps.platform.services import suspend
from apps.reminders.models import ReminderDue
from apps.reminders.services import queue_for
from tests.test_platform import dumbelo, support

MESSAGES = "/api/gym/messages/"
AUTOMATION = "/api/platform/automation/"
JUNE = date(2026, 6, 1)


def console(gym, kind=""):
    return f"/api/platform/gyms/{gym.id}/messages/{f'{kind}/' if kind else ''}"


def at(gym, day, hour, minute=0):
    """A moment on the gym's own clock, as beat would tick it."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=ZoneInfo(gym.timezone))


def switch(gym, *kinds, on=False):
    for kind in kinds:
        NotificationRule.objects.update_or_create(gym=gym, kind=kind, defaults={"is_on": on})


def with_phone(role, phone):
    role.user.phone = phone
    role.user.save(update_fields=["phone"])
    return role


def fresh(gym):
    return Gym.objects.get(pk=gym.pk)


def kinds_sent(gym):
    return sorted(Message.objects.filter(gym=gym).values_list("kind", flat=True))


# ---- Each switch stops its message, and only its message ----

@pytest.mark.parametrize("paused", NotificationRule.REMINDERS)
def test_each_reminder_switch_stops_its_message_and_only_its_message(w, paused):
    w.plan_ending_on(w.today + timedelta(days=7), "Week Left", "9811111117")
    w.plan_ending_on(w.today, "Last Day", "9811111110")
    w.plan_ending_on(w.today + timedelta(days=20), "Owes Money", "9811111120", paid=False)
    switch(w.gym, paused)

    queue_for(w.gym, w.today)
    assert send_due(fresh(w.gym), w.today)["sent"] == 2
    assert kinds_sent(w.gym) == sorted(set(NotificationRule.REMINDERS) - {paused})
    assert ReminderDue.objects.filter(gym=w.gym).count() == 3  # the desk's list is whole: pausing stops messages only


def test_a_paused_reminder_never_stops_another_for_the_same_member(w):
    """A plan ending today outranks money owed; with it paused, the member hears about the money instead."""
    member = w.plan_ending_on(w.today, "Last Day Owing", "9811111100", paid=False)
    switch(w.gym, NotificationRule.PLAN_ENDS_TODAY)
    queue_for(w.gym, w.today)
    send_due(fresh(w.gym), w.today)
    assert Message.objects.get(member=member).kind == NotificationRule.PAYMENT_DUE


def collect(w, c, amount, member=None):
    return c.post("/api/payments/", {"member": (member or w.member).id, "amount_paise": amount, "method": "cash"}, format="json")


def test_receipts_are_off_until_the_gym_turns_them_on_and_each_goes_once(w, django_capture_on_commit_callbacks):
    sell(w.member, w.monthly, by=w.desk)  # ₹1,500 owing
    c = w.client(w.desk)
    with django_capture_on_commit_callbacks(execute=True):
        assert collect(w, c, 50000).status_code == 201
    assert not Message.objects.exists()  # off by default

    switch(w.gym, NotificationRule.PAYMENT_RECEIVED, on=True)
    with django_capture_on_commit_callbacks(execute=True):
        pay_id = collect(w, c, 50000).json()["id"]
    receipt = Message.objects.get()
    assert receipt.kind == NotificationRule.PAYMENT_RECEIVED and receipt.member == w.member and receipt.status == Message.SENT
    assert receipt.dedupe_key == f"payment:{pay_id}" and "received ₹500 from you" in receipt.text

    assert notify.payment_received(pay_id) is None  # a second go finds it on record
    assert Message.objects.count() == 1


def test_a_voided_or_rolled_back_payment_sends_no_receipt(w, django_capture_on_commit_callbacks):
    switch(w.gym, NotificationRule.PAYMENT_RECEIVED, on=True)
    sell(w.member, w.monthly, by=w.desk)
    with django_capture_on_commit_callbacks(execute=True) as queued:
        with pytest.raises(RuntimeError), transaction.atomic():
            take_payment(w.member, 50000, "cash", by=w.desk)
            raise RuntimeError("the desk's request failed after the payment was written")
    assert queued == [] and not Message.objects.exists()

    pay = take_payment(w.member, 50000, "cash", by=w.desk)
    Payment.objects.filter(pk=pay.pk).update(voided=True, void_reason="Typed twice")
    assert notify.payment_received(pay.pk) is None and not Message.objects.exists()


def test_a_task_message_goes_to_the_staff_member_once(w, django_capture_on_commit_callbacks):
    with_phone(w.trainer, "+919811100001")
    with_phone(w.desk, "+919811100002")
    c = w.client(w.admin)
    due = w.today + timedelta(days=1)
    with django_capture_on_commit_callbacks(execute=True):
        task = c.post("/api/tasks/", {"title": "Clean the mats", "assignee": w.trainer.id, "due_date": str(due), "due_time": "17:30"},
                      format="json").json()
    message = Message.objects.get()
    assert message.kind == NotificationRule.TASK_ASSIGNED and message.user == w.trainer.user and message.member is None
    assert message.to == "+919811100001" and "Clean the mats" in message.text and "by 5:30 PM" in message.text

    with django_capture_on_commit_callbacks(execute=True):
        c.patch(f"/api/tasks/{task['id']}/", {"title": "Clean all the mats"}, format="json")
    assert Message.objects.count() == 1  # an edit isn't a new task
    assert notify.task_assigned(task["id"]) is None

    with django_capture_on_commit_callbacks(execute=True):
        c.patch(f"/api/tasks/{task['id']}/", {"assignee": w.desk.id}, format="json")
    assert sorted(Message.objects.values_list("to", flat=True)) == ["+919811100001", "+919811100002"]  # handed on: they hear too


def test_paused_task_messages_and_receipts_send_nothing(w, django_capture_on_commit_callbacks):
    with_phone(w.trainer, "+919811100001")
    switch(w.gym, NotificationRule.TASK_ASSIGNED)
    with django_capture_on_commit_callbacks(execute=True):
        w.client(w.admin).post("/api/tasks/", {"title": "Count the towels", "assignee": w.trainer.id, "due_date": str(w.today)}, format="json")
    assert not Message.objects.exists()


def test_a_gym_with_whatsapp_off_sends_no_receipt_or_task_message(w, django_capture_on_commit_callbacks):
    GymBilling.objects.filter(gym=w.gym).update(whatsapp_mode=GymBilling.OFF)
    with_phone(w.trainer, "+919811100001")
    switch(w.gym, NotificationRule.PAYMENT_RECEIVED, on=True)
    sell(w.member, w.monthly, by=w.desk)
    with django_capture_on_commit_callbacks(execute=True):
        collect(w, w.client(w.desk), 50000)
        w.client(w.admin).post("/api/tasks/", {"title": "Count the towels", "assignee": w.trainer.id, "due_date": str(w.today)}, format="json")
    assert not Message.objects.exists()


# ---- The gym's admins: Pause and Resume, never when ----

def test_an_admin_pauses_and_resumes_a_message_and_it_is_audited(w):
    c = w.client(w.admin)
    rows = c.get(MESSAGES).json()
    assert [r["kind"] for r in rows] == list(NotificationRule.GYM_KINDS)
    by_kind = {r["kind"]: r for r in rows}
    assert by_kind["plan_ending"] == {"kind": "plan_ending", "label": "Plan ending soon", "is_on": True, "switched_by": "gym",
                                      "hour": 6, "days_ahead": [7, 3], "gyms_own_time": False}
    assert by_kind["payment_received"]["is_on"] is False and by_kind["payment_received"]["hour"] is None  # receipts start off
    assert by_kind["task_assigned"]["is_on"] is True

    r = c.patch(f"{MESSAGES}plan_ending/", {"is_on": False}, format="json")
    assert r.status_code == 200 and r.json()["is_on"] is False
    log = AuditLog.objects.get(action="message.switched")
    assert log.gym == w.gym and log.actor == w.admin.user
    assert log.before == {"is_on": True, "hour": 6, "days_ahead": [7, 3]} and log.after["is_on"] is False

    assert c.patch(f"{MESSAGES}plan_ending/", {"is_on": False}, format="json").status_code == 200
    assert AuditLog.objects.filter(action="message.switched").count() == 1  # nothing changed, nothing logged
    assert c.patch(f"{MESSAGES}plan_ending/", {"is_on": True}, format="json").json()["is_on"] is True


def test_a_gyms_admins_cant_set_when_messages_go(w):
    c = w.client(w.admin)
    for body in ({"hour": 9}, {"is_on": False, "hour": 9}, {"is_on": True, "days_ahead": [5]}):
        r = c.patch(f"{MESSAGES}plan_ending/", body, format="json")
        assert r.status_code == 400 and set(r.json()["error"]["fields"]) & {"hour", "days_ahead"}
    assert not NotificationRule.objects.exists()

    assert c.get(AUTOMATION).status_code == 403
    assert c.patch(AUTOMATION, {"reminder_hour": 9}, format="json").status_code == 403
    assert c.patch(console(w.gym, "plan_ending"), {"hour": 9}, format="json").status_code == 403
    # Dumbelo's messages to the owner are Dumbelo's to switch
    assert c.patch(f"{MESSAGES}dumbelo_invoice_due/", {"is_on": False}, format="json").status_code == 404
    assert c.patch(f"{MESSAGES}no_such_message/", {"is_on": False}, format="json").status_code == 404


def test_only_a_gyms_admins_switch_its_messages(w, other):
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(MESSAGES).status_code == 403
        assert c.patch(f"{MESSAGES}plan_ending/", {"is_on": False}, format="json").status_code == 403
    c = w.client(w.admin)
    c.credentials(HTTP_X_GYM=other.gym.slug)
    assert c.get(MESSAGES).status_code == 404
    assert c.patch(f"{MESSAGES}plan_ending/", {"is_on": False}, format="json").status_code == 404
    assert not NotificationRule.objects.exists()


# ---- Dumbelo admins: the times ----

def test_only_dumbelo_admins_change_dumbelos_times_and_it_is_audited(w):
    ops = dumbelo()
    assert ops.get(AUTOMATION).json() == {"reminder_hour": 6, "days_ahead": [7, 3], "invoice_hour": 0, "updated_at": None,
                                          "updated_by_name": None}
    r = ops.patch(AUTOMATION, {"reminder_hour": 7, "days_ahead": [3, 10, 3]}, format="json")
    assert r.status_code == 200 and r.json()["days_ahead"] == [10, 3] and r.json()["updated_by_name"] == "Dumbelo Ops"
    log = AuditLog.objects.get(action="automation.changed")
    assert log.gym is None and log.before == {"reminder_hour": 6, "days_ahead": [7, 3], "invoice_hour": 0}
    assert log.after == {"reminder_hour": 7, "days_ahead": [10, 3], "invoice_hour": 0}

    for body in ({"reminder_hour": 24}, {"invoice_hour": -1}, {"days_ahead": []}, {"days_ahead": [1, 2, 3, 4]}, {"days_ahead": [0]},
                 {"days_ahead": [61]}):
        assert ops.patch(AUTOMATION, body, format="json").status_code == 400, body
    assert AuditLog.objects.filter(action="automation.changed").count() == 1

    for c in (support(), w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(AUTOMATION).status_code == 403
        assert c.patch(AUTOMATION, {"reminder_hour": 9}, format="json").status_code == 403
        assert c.get(console(w.gym)).status_code == 403
        assert c.patch(console(w.gym, "plan_ending"), {"hour": 9}, format="json").status_code == 403


def test_dumbelo_sets_one_gyms_times_and_it_is_audited(w, other):
    ops = dumbelo()
    r = ops.patch(console(w.gym, "plan_ending"), {"hour": 9, "days_ahead": [5]}, format="json")
    assert r.status_code == 200 and r.json() == {"kind": "plan_ending", "label": "Plan ending soon", "is_on": True, "switched_by": "gym",
                                                 "hour": 9, "days_ahead": [5], "gyms_own_time": True}
    log = AuditLog.objects.get(action="message.changed")
    assert log.gym == w.gym and log.before["hour"] == 6 and log.after == {"is_on": True, "hour": 9, "days_ahead": [5]}
    assert {r["kind"]: r["hour"] for r in ops.get(console(other.gym)).json()}["plan_ending"] == 6  # another gym keeps Dumbelo's
    assert {r["kind"]: r["hour"] for r in w.client(w.admin).get(MESSAGES).json()}["plan_ending"] == 9  # the gym sees it

    assert ops.patch(console(w.gym, "payment_received"), {"hour": 9}, format="json").json()["error"]["code"] == "not_scheduled"
    assert ops.patch(console(w.gym, "plan_ends_today"), {"days_ahead": [2]}, format="json").json()["error"]["code"] == "no_days"
    assert ops.patch(console(w.gym, "plan_ending"), {"is_on": False}, format="json").json()["error"]["code"] == "not_yours"
    assert ops.patch(console(w.gym, "plan_ending"), {}, format="json").json()["error"]["code"] == "nothing_to_change"
    assert ops.patch(console(w.gym, "no_such_message"), {"hour": 9}, format="json").status_code == 404
    assert ops.patch("/api/platform/gyms/999999/messages/plan_ending/", {"hour": 9}, format="json").status_code == 404

    r = ops.patch(console(w.gym, "dumbelo_invoice_due"), {"is_on": False}, format="json")
    assert r.status_code == 200 and r.json()["is_on"] is False and r.json()["switched_by"] == "dumbelo"


def test_a_gyms_own_time_beats_dumbelo_and_clearing_it_goes_back(w):
    ops = dumbelo()

    def sends(hour):
        return [sorted(run.send) for run in reminder_runs(at(w.gym, JUNE, hour))]

    assert sends(6) == [sorted(NotificationRule.REMINDERS)] and sends(9) == []
    ops.patch(console(w.gym, "plan_ending"), {"hour": 9}, format="json")
    assert sends(6) == [["payment_due", "plan_ends_today"]] and sends(9) == [["plan_ending"]]

    ops.patch(console(w.gym, "plan_ending"), {"days_ahead": [5]}, format="json")  # its hour stays the gym's own
    assert [run.days_ahead for run in reminder_runs(at(w.gym, JUNE, 9))] == [(5,)]

    r = ops.patch(console(w.gym, "plan_ending"), {"hour": None, "days_ahead": None}, format="json")  # Use Dumbelo's Times
    assert r.json()["gyms_own_time"] is False and r.json()["hour"] == 6 and r.json()["days_ahead"] == [7, 3]
    assert sends(6) == [sorted(NotificationRule.REMINDERS)] and sends(9) == []


def test_times_follow_each_gyms_clock_and_a_change_applies_on_the_next_tick(w, other):
    w.gym.timezone, other.gym.timezone = "Asia/Kolkata", "Europe/London"
    w.gym.save(update_fields=["timezone"])
    other.gym.save(update_fields=["timezone"])
    member = w.plan_ending_on(JUNE + timedelta(days=5), "Five Days", "9811111115")
    ops = dumbelo()
    ops.patch(AUTOMATION, {"reminder_hour": 7, "days_ahead": [5]}, format="json")  # no restart: the next tick reads it

    assert send_reminders.apply(kwargs={"at": "2026-06-01T00:30:00+00:00"}).get() == 0  # 6 AM in Kolkata: not any more
    assert send_reminders.apply(kwargs={"at": "2026-06-01T01:30:00+00:00"}).get() == 1  # 7 AM in Kolkata
    message = Message.objects.get(member=member)
    assert message.kind == NotificationRule.PLAN_ENDING and "in 5 days" in message.text
    assert [r.gym.slug for r in reminder_runs(datetime(2026, 6, 1, 6, 0, tzinfo=ZoneInfo("UTC")))] == ["steel"]  # 7 AM in London


def test_the_invoice_job_waits_for_dumbelos_invoice_hour(w):
    dumbelo().patch(AUTOMATION, {"invoice_hour": 9}, format="json")
    billing_day = date(2026, 11, 1)  # the World's billing day is the 1st
    assert write_due(now=at(w.gym, billing_day, 0, 35)) == 0
    assert write_due(now=at(w.gym, billing_day, 9, 35)) == 1
    assert write_due(now=at(w.gym, billing_day, 10, 35)) == 0  # written already
    assert Invoice.objects.get(gym=w.gym).period_from == billing_day
    assert write_due(day=date(2026, 12, 1)) == 1  # a missed day by hand: any hour


# ---- Dumbelo's messages to the owner ----

def owner_messages(gym, kind=NotificationRule.DUMBELO_INVOICE_DUE):
    return Message.objects.filter(gym=gym, kind=kind)


def test_the_owner_hears_about_an_invoice_before_and_after_its_due_day(w, shared_number):
    with_phone(w.admin, "+919811100009")
    inv = invoicing.write_invoice(w.gym, date(2026, 11, 1))
    assert inv.due_on == date(2026, 11, 8)

    for day in range(1, 17):
        for minute in (0, 15, 30, 45):  # every tick in the owner's hour: one message a day, not four
            notify.invoice_reminders(at(w.gym, date(2026, 11, day), 6, minute))
    sent = owner_messages(w.gym).order_by("for_date")
    assert [m.for_date.day for m in sent] == [5, 9, 15]  # 3 days before, the day after, a week after
    first = sent[0]
    assert first.user == w.admin.user and first.to == "+919811100009" and first.member is None
    assert inv.number in first.text and "₹" in first.text and first.account == shared_number and not first.billable


def test_owner_messages_follow_the_invoice_its_hour_and_dumbelo_switch(w):
    with_phone(w.admin, "+919811100009")
    inv = invoicing.write_invoice(w.gym, date(2026, 11, 1))
    reminder_day = date(2026, 11, 5)
    assert notify.invoice_reminders(at(w.gym, reminder_day, 7)) == 0  # not the hour

    ops = dumbelo()
    ops.patch(console(w.gym, "dumbelo_invoice_due"), {"hour": 7}, format="json")
    switch(w.gym, NotificationRule.DUMBELO_INVOICE_DUE)
    assert notify.invoice_reminders(at(w.gym, reminder_day, 7)) == 0  # paused by Dumbelo
    switch(w.gym, NotificationRule.DUMBELO_INVOICE_DUE, on=True)

    # A suspended gym's owner, with its WhatsApp off, still hears: it comes from Dumbelo's number
    suspend(w.gym, "Not paid")
    GymBilling.objects.filter(gym=w.gym).update(whatsapp_mode=GymBilling.OFF)
    assert notify.invoice_reminders(at(w.gym, reminder_day, 7)) == 1

    invoicing.record_payment(inv, amount_paise=inv.total_paise, method="bank", paid_on=date(2026, 10, 18), by=w.admin.user)
    assert notify.invoice_reminders(at(w.gym, date(2026, 11, 9), 7)) == 0  # paid: nothing to chase


def test_the_owner_hears_once_that_dumbelo_got_their_payment(w, django_capture_on_commit_callbacks):
    with_phone(w.admin, "+919811100009")
    inv = invoicing.write_invoice(w.gym, date(2026, 11, 1))
    ops = dumbelo()
    body = {"amount_paise": 100000, "method": "bank", "paid_on": "2026-10-18", "reference": "UTR123"}
    with django_capture_on_commit_callbacks(execute=True):
        assert ops.post(f"/api/platform/invoices/{inv.id}/payments/", body, format="json").status_code == 200
    pay = inv.payments.get()
    message = owner_messages(w.gym, NotificationRule.DUMBELO_PAYMENT_RECEIVED).get()
    assert message.user == w.admin.user and pay.receipt_number in message.text and "₹1,000" in message.text
    assert notify.dumbelo_payment_received(pay.id) is None

    ops.patch(console(w.gym, "dumbelo_payment_received"), {"is_on": False}, format="json")
    with django_capture_on_commit_callbacks(execute=True):
        ops.post(f"/api/platform/invoices/{inv.id}/payments/", body, format="json")
    assert owner_messages(w.gym, NotificationRule.DUMBELO_PAYMENT_RECEIVED).count() == 1


# ---- Query budgets ----

def test_the_message_lists_cost_the_same_however_many_rules(w, django_assert_max_num_queries):
    ops, c = dumbelo(), w.client(w.admin)
    # Counted at once: each request clears Django's query log, and with it what an earlier block captured
    with django_assert_max_num_queries(10) as few:
        c.get(MESSAGES)
    gym_reads = len(few.captured_queries)
    with django_assert_max_num_queries(6) as few:
        ops.get(console(w.gym))
    console_reads = len(few.captured_queries)
    for kind in NotificationRule.SCHEDULED:
        ops.patch(console(w.gym, kind), {"hour": 8}, format="json")
    switch(w.gym, *NotificationRule.GYM_KINDS)
    with django_assert_max_num_queries(gym_reads):
        assert all(not r["is_on"] for r in c.get(MESSAGES).json())
    with django_assert_max_num_queries(console_reads):
        assert len(ops.get(console(w.gym)).json()) == 7


# ---- What came before ----

@pytest.mark.django_db(transaction=True)
def test_the_migration_carries_reminders_off_and_old_reminder_kinds_over(w, other):
    """A gym that had reminders off gets its three reminders paused, and the day's list keeps how many days were left."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    before = [("gym_messages", "0005_webhook"), ("reminders", "0001_initial")]  # takes the gyms field back with it
    executor.migrate(before)
    old = executor.loader.project_state(before).apps
    old.get_model("gyms", "Gym").objects.filter(pk=w.gym.pk).update(reminders_on=False)
    OldDue = old.get_model("reminders", "ReminderDue")
    for kind, member in (("expiring_7", w.member), ("dues", other.member)):
        OldDue.objects.create(gym_id=member.gym_id, member_id=member.pk, kind=kind, for_date=JUNE)
    MigrationExecutor(connection).migrate(executor.loader.graph.leaf_nodes())

    paused = NotificationRule.objects.filter(gym=w.gym, is_on=False).values_list("kind", flat=True)
    assert sorted(paused) == sorted(NotificationRule.REMINDERS) and not NotificationRule.objects.filter(gym=other.gym).exists()
    assert ReminderDue.objects.get(member=w.member).kind == "plan_ending" and ReminderDue.objects.get(member=w.member).days_left == 7
    assert ReminderDue.objects.get(member=other.member).kind == "payment_due"
