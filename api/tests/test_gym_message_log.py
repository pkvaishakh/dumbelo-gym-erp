"""More → Messages: the gym's own log, with filters and search, and Retry for a message that failed."""
from datetime import timedelta

import pytest

from apps.audit.models import AuditLog
from apps.billing.models import GymBilling
from apps.billing.services import change_plan
from apps.messages.models import Message, NotificationRule, WhatsAppTemplate
from apps.messages.senders import FakeSender
from apps.platform.services import suspend

LOG = "/api/messages/"


def message(w, n, *, to=None, kind="plan_ending", status=Message.DELIVERED, for_date=None, account=None, **extra):
    """A message the gym sent, from the shared number unless it says otherwise. To the member unless `to` is a staff role."""
    template = WhatsAppTemplate.objects.filter(account__gym=None, kind=kind).first() if account is None else None
    person = {"user": to.user} if to is not None and hasattr(to, "role") else {"member": to or w.member}
    phone = (to.user.phone if "user" in person else person["member"].phone) or "+919811100000"
    return Message.objects.create(gym=w.gym, kind=kind, dedupe_key=f"t:{n}", to=phone, text=f"Message {n}", for_date=for_date or w.today,
                                  provider="fake", status=status, account=account or (template.account if template else None),
                                  template=template, **person, **extra)


def failed(w, n=1, **extra):
    """A reminder Meta refused: it never reached the phone, so it may be sent again."""
    extra.setdefault("error", "Message undeliverable (code 131026)")
    extra.setdefault("error_code", "131026")
    return message(w, n, status=Message.FAILED, attempts=1, **extra)


def ids(r):
    assert r.status_code == 200, r.content
    return [m["id"] for m in r.json()["results"]]


# ---- The log ----

def test_the_admin_reads_every_message_with_who_it_went_to(w, django_assert_max_num_queries):
    w.admin.user.phone = "+919800000099"
    w.admin.user.save()
    for n in range(5):
        message(w, n)
    staff = message(w, 9, to=w.admin, kind="task_assigned")

    with django_assert_max_num_queries(6):
        r = w.client(w.admin).get(LOG)

    body = r.json()
    assert body["count"] == 6
    row = next(m for m in body["results"] if m["id"] == staff.pk)
    assert row["recipient"] == "staff" and row["to_name"] == w.admin.user.name and row["member"] is None
    member_row = next(m for m in body["results"] if m["id"] != staff.pk)
    assert member_row["to_name"] == "Asha" and member_row["status_label"] == "Delivered" and member_row["can_retry"] is False


def test_the_log_filters_by_status_message_recipient_and_days(w):
    w.trainer.user.phone = "+919800000098"
    w.trainer.user.save()
    old = message(w, 1, for_date=w.today - timedelta(days=10))
    bad = failed(w, 2, kind="payment_due")
    staff = message(w, 3, to=w.trainer, kind="task_assigned")
    admin = w.client(w.admin)

    assert ids(admin.get(LOG, {"status": "failed"})) == [bad.pk]
    assert ids(admin.get(LOG, {"kind": "payment_due"})) == [bad.pk]
    assert ids(admin.get(LOG, {"recipient": "staff"})) == [staff.pk]
    assert set(ids(admin.get(LOG, {"recipient": "member"}))) == {old.pk, bad.pk}
    assert set(ids(admin.get(LOG, {"from": (w.today - timedelta(days=1)).isoformat()}))) == {bad.pk, staff.pk}
    assert ids(admin.get(LOG, {"to": (w.today - timedelta(days=5)).isoformat()})) == [old.pk]


def test_bad_filters_answer_with_the_field(w):
    admin = w.client(w.admin)
    for params, field in (({"recipient": "everyone"}, "recipient"), ({"from": "yesterday"}, "from"),
                          ({"from": w.today.isoformat(), "to": (w.today - timedelta(days=1)).isoformat()}, "from")):
        r = admin.get(LOG, params)
        assert r.status_code == 400 and field in r.json()["error"]["fields"], params


def test_search_finds_a_name_or_the_end_of_a_number(w):
    ravi = w.new_member("Ravi Kumar", "9811122233", w.a)
    theirs, asha = message(w, 1, to=ravi), message(w, 2)
    admin = w.client(w.admin)

    assert ids(admin.get(LOG, {"q": "ravi"})) == [theirs.pk]
    assert ids(admin.get(LOG, {"q": "2233"})) == [theirs.pk]
    assert ids(admin.get(LOG, {"q": "+91 98111 22233"})) == [theirs.pk]
    assert set(ids(admin.get(LOG, {"q": "a"}))) == {theirs.pk, asha.pk}  # one letter: no search yet


def test_the_desk_reads_only_its_branches_members_messages(w):
    w.admin.user.phone = "+919800000099"
    w.admin.user.save()
    at_a = message(w, 1)
    message(w, 2, to=w.new_member("Bina", "9811100002", w.b))
    message(w, 3, to=w.admin, kind="task_assigned")
    assert ids(w.client(w.desk).get(LOG)) == [at_a.pk]


def test_trainers_and_members_cant_read_the_log(w):
    message(w, 1)
    for c in (w.client(w.trainer), w.member_client()):
        assert c.get(LOG).status_code == 403


# ---- Retry ----

def retry(c, row):
    return c.post(f"{LOG}{row.pk}/retry/")


def test_retry_sends_a_failed_message_again_on_the_same_row(w):
    row = failed(w)
    assert w.client(w.admin).get(LOG).json()["results"][0]["can_retry"] is True

    r = retry(w.client(w.admin), row)

    assert r.status_code == 200, r.content
    assert r.json()["status"] == "sent" and r.json()["error"] == ""
    row.refresh_from_db()
    assert row.status == Message.SENT and row.attempts == 2 and row.error_code == "" and row.dedupe_key == "t:1"
    assert FakeSender.outbox == [(w.member.phone, "Message 1")]
    assert Message.objects.filter(gym=w.gym).count() == 1
    log = AuditLog.objects.get(action="message.retried")
    assert log.before["status"] == "failed" and log.after["status"] == "sent"


def test_retry_goes_to_their_number_as_it_is_now(w):
    row = failed(w)
    w.member.phone = "+919811199999"
    w.member.save()
    retry(w.client(w.admin), row)
    row.refresh_from_db()
    assert row.to == "+919811199999" and FakeSender.outbox[-1][0] == "+919811199999"


def test_a_second_retry_finds_it_already_gone(w):
    row = failed(w)
    admin = w.client(w.admin)
    assert retry(admin, row).status_code == 200
    r = retry(admin, row)
    assert r.status_code == 409 and r.json()["error"]["code"] == "cant_retry"
    assert len(FakeSender.outbox) == 1


def test_two_admins_pressing_retry_together_send_it_once(w):
    """The row is taken by whoever changes it first: the other finds it isn't failed any more."""
    from apps.messages import services

    row = failed(w)
    stale = Message.objects.get(pk=row.pk)  # the second admin's copy, read before the first one's retry
    services.retry(row)
    with pytest.raises(services.RuleBroken) as e:
        services.retry(stale)
    assert e.value.rule_code == "already_retried" and len(FakeSender.outbox) == 1


@pytest.mark.parametrize("code", ["no_answer", "bad_answer", "interrupted", "send_error"])
def test_a_message_that_may_have_gone_is_never_retried(w, code):
    row = failed(w, error="Meta didn't answer", error_code=code)
    assert w.client(w.admin).get(LOG).json()["results"][0]["can_retry"] is False
    r = retry(w.client(w.admin), row)
    assert r.status_code == 409 and "may have reached them" in r.json()["error"]["message"]
    assert FakeSender.outbox == []


def test_only_a_failed_message_written_out_in_full_can_go_again(w):
    admin = w.client(w.admin)
    sent = message(w, 1, status=Message.SENT)
    never_written = failed(w, 2, error="Not sent: WhatsApp isn't set up for your gym yet.", error_code="")
    Message.objects.filter(pk=never_written.pk).update(template=None, account=None)
    owner = failed(w, 3, kind=NotificationRule.RACKLINE_INVOICE_DUE)  # Rackline's own, to the owner
    for row in (sent, never_written, owner):
        assert retry(admin, row).status_code == 409
    assert FakeSender.outbox == []


@pytest.mark.parametrize("why, expect", [
    ("archived", "archived"), ("paused", "paused"), ("opted_out", "asked not to"), ("off", "off for your gym"), ("suspended", "Rackline account is paused"),
    ("no_number", "mobile number"), ("own_number", "different WhatsApp number"), ("template_off", "isn't approved"),
])
def test_retry_says_why_it_cant_go_now(w, why, expect):
    row = failed(w)
    if why == "archived":
        w.member.is_archived = True
        w.member.save()
    elif why == "paused":
        NotificationRule.objects.create(gym=w.gym, kind="plan_ending", is_on=False)
    elif why == "opted_out":
        w.member.reminders_opted_out = True
        w.member.save()
    elif why == "off":
        change_plan(w.gym, whatsapp_mode=GymBilling.OFF)
    elif why == "suspended":
        suspend(w.gym, reason="Unpaid")
    elif why == "no_number":
        w.member.phone = ""
        w.member.save()
    elif why == "own_number":
        from tests.test_message_log import own_number

        own_number(w)
        change_plan(w.gym, whatsapp_mode=GymBilling.OWN)
    else:
        WhatsAppTemplate.objects.filter(pk=row.template_id).update(status=WhatsAppTemplate.DISABLED)

    r = retry(w.client(w.admin), row)

    if why == "suspended":  # a paused gym's app is shut, so the API turns it away before Retry is asked
        assert r.status_code == 403 and r.json()["error"]["code"] == "gym_suspended"
    else:
        assert r.status_code == 409, r.content
        assert expect in r.json()["error"]["message"]
    row.refresh_from_db()
    assert row.status == Message.FAILED and FakeSender.outbox == []


def test_only_admins_retry_and_never_another_gyms(w, other):
    row = failed(w)
    for c in (w.client(w.desk), w.client(w.trainer)):
        assert retry(c, row).status_code == 403
    assert retry(other.client(other.admin), row).status_code == 404
    assert FakeSender.outbox == []


# ---- Retry sends the words as written, so they must still be true ----

def refused(w, row, words):
    r = retry(w.client(w.admin), row)
    assert r.status_code == 409 and words in r.json()["error"]["message"], r.content
    assert FakeSender.outbox == []


def test_a_reminder_goes_again_only_on_its_own_day(w):
    refused(w, failed(w, for_date=w.today - timedelta(days=1)), "Today's reminders go out on their own")


def test_a_reminder_that_no_longer_fits_their_plan_isnt_sent(w):
    """'Your plan ends in 3 days', after the desk froze it."""
    sub = w.member.current_subscription(w.today)
    sub.frozen_from = w.today
    sub.save()
    refused(w, failed(w), "no longer fits")


def owing(w, amount="₹1,000"):
    """Asha, owing ₹1,000 on a ₹1,500 plan, and the payment due reminder that told her so."""
    from apps.members.models import Payment

    Payment.objects.filter(member=w.member).update(voided=True)
    from apps.members.services import take_payment

    take_payment(w.member, 50000, "cash", by=w.desk)
    return failed(w, kind="payment_due", parameters=["Asha", amount])


def test_money_owed_goes_again_while_they_still_owe_the_same(w):
    row = owing(w)
    assert retry(w.client(w.admin), row).json()["status"] == "sent"


def test_money_owed_isnt_sent_once_they_paid_or_the_amount_changed(w):
    from apps.members.services import take_payment

    row = owing(w)
    take_payment(w.member, 20000, "cash", by=w.desk)
    refused(w, row, "What they owe has changed")
    take_payment(w.member, 80000, "cash", by=w.desk)
    refused(w, row, "They've paid since")


def test_a_receipt_for_a_voided_payment_isnt_sent(w):
    from apps.members.models import Payment

    NotificationRule.objects.create(gym=w.gym, kind="payment_received", is_on=True)  # receipts are off until a gym turns them on
    pay = Payment.objects.filter(member=w.member).first()
    row = failed(w, kind="payment_received")
    Message.objects.filter(pk=row.pk).update(dedupe_key=f"payment:{pay.pk}")
    row.refresh_from_db()
    Payment.objects.filter(pk=pay.pk).update(voided=True)
    refused(w, row, "voided")


def test_a_task_message_goes_again_only_while_the_task_is_theirs_and_open(w):
    from apps.tasks.models import Task

    w.trainer.user.phone = "+919800000098"
    w.trainer.user.save()
    task = Task.objects.create(gym=w.gym, title="Clean the mats", assignee=w.trainer, created_by=w.admin, due_date=w.today)
    row = message(w, 1, to=w.trainer, kind="task_assigned", status=Message.FAILED, attempts=1, error_code="131026", error="Undeliverable")
    Message.objects.filter(pk=row.pk).update(dedupe_key=f"task:{task.pk}:to:{w.trainer.pk}")
    row.refresh_from_db()

    Task.objects.filter(pk=task.pk).update(assignee=w.desk)
    refused(w, row, "with someone else")
    Task.objects.filter(pk=task.pk).update(assignee=w.trainer, status=Task.DONE)
    refused(w, row, "task is done")
    Task.objects.filter(pk=task.pk).update(status=Task.TODO)
    assert retry(w.client(w.admin), row).json()["status"] == "sent"
