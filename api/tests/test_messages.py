"""The reminders that reach members: who gets one, how often, and what is written down when one fails."""
from datetime import timedelta

from apps.members.models import Member
from apps.messages.models import Message, NotificationRule
from apps.messages.senders import FakeSender, SendFailed
from apps.messages.services import send_due
from apps.messages.tasks import send_reminders
from apps.reminders.models import ReminderDue
from apps.reminders.services import queue_for

SETTINGS = "/api/gym/settings/"


def nudge(w, day=None):
    """Work out the gym's reminders for a local day and send them, the way the morning job does."""
    day = day or w.today
    queue_for(w.gym, day)
    return send_due(w.gym, day)


def test_a_plan_ending_in_a_week_is_asked_to_renew(w):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Asha Rao", "9811111117")

    assert nudge(w) == {"sent": 1, "failed": 0, "skipped": 0}

    message = Message.objects.get(gym=w.gym, member=member)
    assert message.status == Message.SENT and message.kind == ReminderDue.PLAN_ENDING
    assert message.to == member.phone and message.provider == "fake" and message.provider_id and message.error == ""
    assert message.text.startswith("Hi Asha,")  # their first name, not "Dear Member"
    assert "Monthly plan" in message.text and "in 7 days" in message.text and "front desk" in message.text
    assert FakeSender.outbox == [(member.phone, message.text)]  # and nothing else left the building


def test_a_member_who_owes_money_is_told_how_much(w):
    member = w.plan_ending_on(w.today + timedelta(days=20), "Vikram Shah", "9811111120", paid=False)

    assert nudge(w)["sent"] == 1

    message = Message.objects.get(member=member)
    assert message.kind == ReminderDue.PAYMENT_DUE
    assert "₹1,500 is still to pay" in message.text and "Monthly plan" in message.text


def test_a_member_hears_once_a_day(w):
    """A plan ending today and money owed is two reminders and one message: the more pressing one."""
    member = w.plan_ending_on(w.today, "Karthik Iyer", "9811111100", paid=False)
    queue_for(w.gym, w.today)
    assert sorted(ReminderDue.objects.filter(member=member).values_list("kind", flat=True)) == ["payment_due", "plan_ends_today"]

    assert send_due(w.gym, w.today)["sent"] == 1
    message = Message.objects.get(member=member)
    assert message.kind == ReminderDue.PLAN_ENDS_TODAY and "ends today" in message.text

    assert send_due(w.gym, w.today) == {"sent": 0, "failed": 0, "skipped": 0}  # run again: nothing to send
    assert Message.objects.filter(member=member).count() == 1 and len(FakeSender.outbox) == 1


def test_tomorrow_is_its_own_message(w):
    """One a day, not one for ever: a member still owing money tomorrow hears again tomorrow."""
    member = w.plan_ending_on(w.today + timedelta(days=20), "Still Owing", "9811111121", paid=False)
    nudge(w)
    assert nudge(w, w.today + timedelta(days=1))["sent"] == 1
    assert Message.objects.filter(member=member).count() == 2


def test_a_member_who_asked_us_to_stop_is_left_alone(w):
    quiet = w.plan_ending_on(w.today + timedelta(days=3), "Quiet One", "9811111103")
    Member.objects.filter(pk=quiet.pk).update(reminders_opted_out=True)
    chatty = w.plan_ending_on(w.today + timedelta(days=3), "Happy To Hear", "9811111104")

    assert nudge(w) == {"sent": 1, "failed": 0, "skipped": 1}

    assert not Message.objects.filter(member=quiet).exists()
    assert Message.objects.filter(member=chatty).exists()
    assert ReminderDue.objects.filter(member=quiet).exists()  # the desk still sees them on the day's list


def test_a_member_with_no_number_is_skipped(w):
    member = w.plan_ending_on(w.today + timedelta(days=3), "No Number", "9811111105")
    Member.objects.filter(pk=member.pk).update(phone="")

    assert nudge(w) == {"sent": 0, "failed": 0, "skipped": 1}
    assert Message.objects.count() == 0 and FakeSender.outbox == []


def test_a_failed_send_is_written_down_and_the_rest_still_go(w, monkeypatch):
    bad = w.plan_ending_on(w.today + timedelta(days=3), "Bad Number", "9811111106")
    good = w.plan_ending_on(w.today + timedelta(days=3), "Good Number", "9811111107")

    def refuse_one(self, to, text):
        if to == bad.phone:
            raise SendFailed("That isn't a WhatsApp number")
        return "sent-ok"

    monkeypatch.setattr(FakeSender, "send", refuse_one)
    assert nudge(w) == {"sent": 1, "failed": 1, "skipped": 0}

    failed = Message.objects.get(member=bad)
    assert failed.status == Message.FAILED and failed.error == "That isn't a WhatsApp number" and failed.provider_id == ""
    assert Message.objects.get(member=good).status == Message.SENT  # one bad number doesn't stop the morning


def test_a_provider_that_breaks_doesnt_stop_the_morning(w, monkeypatch):
    """Not every provider raises SendFailed: whatever its client throws is one member's problem, not the gym's."""
    member = w.plan_ending_on(w.today + timedelta(days=3), "First In Line", "9811111108")
    w.plan_ending_on(w.today + timedelta(days=3), "Second In Line", "9811111109")

    def break_once(self, to, text):
        if to == member.phone:
            raise RuntimeError("Connection reset by peer")
        return "sent-ok"

    monkeypatch.setattr(FakeSender, "send", break_once)
    assert nudge(w) == {"sent": 1, "failed": 1, "skipped": 0}
    assert Message.objects.get(member=member).error == "Connection reset by peer"


def test_a_gym_with_its_reminders_paused_sends_nothing(w):
    NotificationRule.objects.bulk_create([NotificationRule(gym=w.gym, kind=k, is_on=False) for k in NotificationRule.REMINDERS])
    w.plan_ending_on(w.today + timedelta(days=7), "Not Messaged", "9811111110")

    assert nudge(w) == {"sent": 0, "failed": 0, "skipped": 0}
    assert ReminderDue.objects.filter(gym=w.gym).count() == 1  # the list is still there to turn back on
    assert Message.objects.count() == 0 and FakeSender.outbox == []


def test_each_gym_only_messages_its_own_members(w, other):
    mine = w.plan_ending_on(w.today + timedelta(days=7), "Mine", "9811111111")
    other.plan_ending_on(other.today + timedelta(days=7), "Theirs", "9811111111")

    queue_for(other.gym, other.today)
    assert nudge(w)["sent"] == 1

    assert [m.member_id for m in Message.objects.all()] == [mine.id]
    assert not Message.objects.filter(gym=other.gym).exists()  # their morning is their own


def test_the_morning_job_lists_and_sends_in_one_go(w, other):
    """The task beat runs, as the worker would run it: eager here, because no broker is set."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    w.gym.timezone, other.gym.timezone = "Asia/Kolkata", "Europe/London"
    w.gym.save(update_fields=["timezone"])
    other.gym.save(update_fields=["timezone"])
    sweep_day = datetime(2026, 6, 1).date()
    member = w.plan_ending_on(sweep_day + timedelta(days=3), "Three Days", "9811111113")

    at = datetime(2026, 6, 1, 0, 30, tzinfo=ZoneInfo("UTC")).isoformat()  # 6:00 AM in Kolkata
    assert send_reminders.apply(kwargs={"at": at}).get() == 1

    message = Message.objects.get(member=member)
    assert message.for_date == sweep_day and message.kind == ReminderDue.PLAN_ENDING
    assert not Message.objects.filter(gym=other.gym).exists()  # London is still asleep


def test_the_reads_dont_grow_with_the_number_of_members(w, django_assert_max_num_queries):
    """Each message costs one write; working out who to write to must not cost one query a member."""
    for i in range(2):
        w.plan_ending_on(w.today + timedelta(days=7), f"Two {i}", f"97{6000 + i:08d}")
    queue_for(w.gym, w.today)
    with django_assert_max_num_queries(12) as few:  # 2 of them the gym's switches and Dumbelo's schedule
        send_due(w.gym, w.today)
    reads = len(few.captured_queries) - 2  # two members, two inserts

    day = w.today + timedelta(days=1)
    for i in range(2, 10):
        w.plan_ending_on(day + timedelta(days=7), f"Ten {i}", f"97{6000 + i:08d}")
    queue_for(w.gym, day)
    with django_assert_max_num_queries(reads + 10):
        send_due(w.gym, day)


# ---- what the desk can read ----

def test_the_desk_reads_the_reminders_a_member_got(w):
    member = w.plan_ending_on(w.today + timedelta(days=7), "Asha Rao", "9811111117")
    nudge(w)

    rows = w.client(w.desk).get(f"/api/messages/?member={member.id}").json()["results"]
    assert len(rows) == 1
    row = rows[0]
    assert row["member"] == member.id and row["member_name"] == "Asha Rao"
    assert row["kind"] == "plan_ending" and row["kind_label"] == "Plan ending soon" and row["status"] == "sent"
    assert row["for_date"] == str(w.today) and "Hi Asha," in row["text"] and row["to"] == member.phone


def test_trainers_and_members_cant_read_reminders(w):
    """A dues reminder says the amount, so the two roles that never see amounts don't see these either."""
    w.plan_ending_on(w.today + timedelta(days=7), "Asha Rao", "9811111117")
    nudge(w)

    assert w.client(w.trainer).get("/api/messages/").status_code == 403
    assert w.member_client().get("/api/messages/").status_code == 403


def test_another_gyms_reminder_is_not_found(w, other):
    other.plan_ending_on(other.today + timedelta(days=7), "Theirs", "9811111117")
    queue_for(other.gym, other.today)
    send_due(other.gym, other.today)
    theirs = Message.objects.get(gym=other.gym)

    c = w.client(w.admin)
    assert c.get(f"/api/messages/{theirs.id}/").status_code == 404
    assert c.get("/api/messages/").json()["count"] == 0


def test_a_receptionist_only_reads_their_own_branches(w):
    member = w.plan_ending_on(w.today + timedelta(days=7), "At Branch A", "9811111117")
    nudge(w)

    assert w.client(w.desk).get("/api/messages/").json()["count"] == 1
    assert w.client(w.desk_b).get("/api/messages/").json()["count"] == 0  # branch B's desk, branch A's member
    assert w.client(w.desk_b).get(f"/api/messages/{Message.objects.get(member=member).id}/").status_code == 404


def test_the_reminder_list_costs_the_same_however_many_rows(w, django_assert_max_num_queries):
    for i in range(3):
        day = w.today - timedelta(days=i)
        w.plan_ending_on(day + timedelta(days=7), f"Three {i}", f"97{7000 + i:08d}")
        nudge(w, day)
    c = w.client(w.admin)
    with django_assert_max_num_queries(6) as few:
        assert c.get("/api/messages/").json()["count"] == 3

    for i in range(3, 12):
        day = w.today - timedelta(days=i)
        w.plan_ending_on(day + timedelta(days=7), f"Twelve {i}", f"97{7000 + i:08d}")
        nudge(w, day)
    with django_assert_max_num_queries(len(few.captured_queries)):
        assert c.get("/api/messages/").json()["count"] == 12


# ---- the gym's settings ----

def test_the_settings_say_how_dumbelo_set_the_gym_up_and_change_nothing(w):
    c = w.client(w.admin)
    assert c.get(SETTINGS).json() == {"name": w.gym.name, "slug": "iron", "timezone": "Asia/Kolkata"}
    assert c.patch(SETTINGS, {"name": "Not My Gym", "timezone": "Europe/London"}, format="json").status_code == 405
    w.gym.refresh_from_db()
    assert w.gym.name != "Not My Gym" and w.gym.timezone == "Asia/Kolkata"


def test_only_admins_see_the_settings(w, other):
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(SETTINGS).status_code == 403
    c = w.client(w.admin)
    c.credentials(HTTP_X_GYM=other.gym.slug)
    assert c.get(SETTINGS).status_code == 404
