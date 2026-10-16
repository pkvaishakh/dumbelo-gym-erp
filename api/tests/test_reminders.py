"""The daily reminder list: who it picks in each gym's own time zone, and what it leaves alone."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from apps.core import clock
from apps.members.models import Member
from apps.members.services import sell, take_payment
from apps.reminders.models import ReminderDue
from apps.reminders.services import due_for, gyms_at_reminder_hour, queue_for
from apps.reminders.tasks import sweep_reminders


def ending_in(w, days, name="Ending", phone="9811111111", paid=True):
    """A member at branch A whose plan runs out `days` from the gym's today."""
    m = w.new_member(name, phone, w.a)
    sub = sell(m, w.monthly, by=w.desk, starts=w.today + timedelta(days=days) - timedelta(days=w.monthly.months * 30 - 1))
    sub.ends = w.today + timedelta(days=days)
    sub.save(update_fields=["ends"])
    if paid:
        take_payment(m, sub.price_paise, "cash", by=w.desk)
    return m


def plan_ending_on(w, day, name, phone, paid=True):
    """A member whose plan runs out on an exact date, for the days the test fixes rather than today's."""
    m = w.new_member(name, phone, w.a)
    sub = sell(m, w.monthly, by=w.desk, starts=day - timedelta(days=30))
    sub.ends = day
    sub.save(update_fields=["ends"])
    if paid:
        take_payment(m, sub.price_paise, "cash", by=w.desk)
    return m


def kinds_for(gym, day, member):
    return sorted(ReminderDue.objects.filter(gym=gym, member=member, for_date=day).values_list("kind", flat=True))


def test_it_picks_plans_ending_in_seven_three_and_zero_days(w):
    seven = ending_in(w, 7, "Seven", "9811111117")
    three = ending_in(w, 3, "Three", "9811111113")
    today = ending_in(w, 0, "Today", "9811111110")
    ending_in(w, 5, "Five", "9811111115")  # no reminder on the days in between
    ending_in(w, 30, "Later", "9811111130")

    assert queue_for(w.gym, w.today) == 3  # the three above; the five- and thirty-day ones are not due anything

    assert kinds_for(w.gym, w.today, seven) == ["expiring_7"]
    assert kinds_for(w.gym, w.today, three) == ["expiring_3"]
    assert kinds_for(w.gym, w.today, today) == ["expiring_0"]
    assert ReminderDue.objects.filter(gym=w.gym, kind="expiring_7").count() == 1


def test_a_member_who_owes_money_is_chased(w):
    owing = ending_in(w, 20, "Owing", "9811111120", paid=False)
    assert kinds_for(w.gym, w.today, owing) == []
    queue_for(w.gym, w.today)
    assert kinds_for(w.gym, w.today, owing) == ["dues"]


def test_a_plan_ending_with_money_owed_earns_both(w):
    both = ending_in(w, 3, "Both", "9811111103", paid=False)
    queue_for(w.gym, w.today)
    assert kinds_for(w.gym, w.today, both) == ["dues", "expiring_3"]


def test_archived_and_frozen_members_are_left_alone(w):
    archived = ending_in(w, 3, "Archived", "9811111199", paid=False)
    archived.is_archived = True
    archived.save(update_fields=["is_archived"])

    frozen = ending_in(w, 3, "Frozen", "9811111198", paid=False)
    sub = frozen.subscriptions.get()
    sub.frozen_from, sub.frozen_until = w.today - timedelta(days=1), w.today + timedelta(days=10)
    sub.save(update_fields=["frozen_from", "frozen_until"])

    queue_for(w.gym, w.today)
    assert kinds_for(w.gym, w.today, archived) == []  # they left the gym
    assert kinds_for(w.gym, w.today, frozen) == []  # a paused plan isn't running out, and isn't chased for money


def test_running_it_twice_adds_nothing(w):
    ending_in(w, 7, "Seven", "9811111117")
    first = queue_for(w.gym, w.today)
    before = list(ReminderDue.objects.filter(gym=w.gym).values_list("id", flat=True))
    assert first > 0 and queue_for(w.gym, w.today) == 0
    assert list(ReminderDue.objects.filter(gym=w.gym).values_list("id", flat=True)) == before


def test_tomorrow_is_its_own_day(w):
    """The same member can be reminded again on another day: the constraint is per day, not for ever."""
    member = ending_in(w, 10, "Owing", "9811111120", paid=False)
    queue_for(w.gym, w.today)
    assert queue_for(w.gym, w.today + timedelta(days=1)) > 0
    assert ReminderDue.objects.filter(gym=w.gym, member=member, kind="dues").count() == 2


def test_each_gym_only_gets_its_own_members(w, other):
    ending_in(w, 7, "Mine", "9811111117")
    queue_for(w.gym, w.today)
    assert ReminderDue.objects.filter(gym=other.gym).count() == 0
    assert all(r.member.gym_id == w.gym.id for r in ReminderDue.objects.filter(gym=w.gym).select_related("member"))


@pytest.mark.django_db
def test_six_in_the_morning_means_six_where_the_gym_is(w, other):
    """Two gyms, two time zones: each gets its list when its own clock says 6, not the server's."""
    w.gym.timezone, other.gym.timezone = "Asia/Kolkata", "Europe/London"
    w.gym.save(update_fields=["timezone"])
    other.gym.save(update_fields=["timezone"])

    # 00:30 UTC is 6:00 in Kolkata and 1:30 in London
    at = datetime(2026, 6, 1, 0, 30, tzinfo=ZoneInfo("UTC"))
    assert [g.slug for g, _ in gyms_at_reminder_hour(at)] == ["iron"]

    # five hours later it is London's turn, and Kolkata has moved on
    at = datetime(2026, 6, 1, 5, 30, tzinfo=ZoneInfo("UTC"))
    assert [g.slug for g, _ in gyms_at_reminder_hour(at)] == ["steel"]

    # and the day each one gets is its own local day
    at = datetime(2026, 6, 1, 0, 30, tzinfo=ZoneInfo("UTC"))
    assert [day for _, day in gyms_at_reminder_hour(at)] == [datetime(2026, 6, 1).date()]


def test_a_half_hour_time_zone_is_woken_at_its_own_six(w):
    """India is UTC+5:30, so beat has to tick inside the hour or Bengaluru's 6 AM list goes out at 6:30."""
    from django.conf import settings

    w.gym.timezone = "Asia/Kolkata"
    w.gym.save(update_fields=["timezone"])
    minutes = settings.CELERY_BEAT_SCHEDULE["reminders"]["schedule"].minute
    ticks = [datetime(2026, 6, 1, 0, m, tzinfo=ZoneInfo("UTC")) for m in sorted(minutes)]
    six = [clock.local(w.gym, t) for t in ticks if list(gyms_at_reminder_hour(t))]
    assert six and min(t.strftime("%H:%M") for t in six) == "06:00"


def test_a_suspended_gym_is_skipped(w):
    w.gym.status = "suspended"
    w.gym.save(update_fields=["status"])
    at = datetime.now(ZoneInfo("Asia/Kolkata")).replace(hour=6, minute=0)
    assert list(gyms_at_reminder_hour(at)) == []


def test_the_scheduled_job_writes_the_rows_for_the_gyms_it_wakes(w, other):
    """The task itself, run as the worker would: eager here, because no broker is set."""
    w.gym.timezone, other.gym.timezone = "Asia/Kolkata", "Europe/London"
    w.gym.save(update_fields=["timezone"])
    other.gym.save(update_fields=["timezone"])
    sweep_day = datetime(2026, 6, 1).date()
    member = plan_ending_on(w, sweep_day + timedelta(days=7), "Seven", "9811111117")

    at = datetime(2026, 6, 1, 0, 30, tzinfo=ZoneInfo("UTC")).isoformat()
    assert sweep_reminders.apply(kwargs={"at": at}).get() == 1
    assert kinds_for(w.gym, sweep_day, member) == ["expiring_7"]
    assert not ReminderDue.objects.filter(gym=other.gym).exists()  # London is still asleep


def test_the_list_costs_the_same_however_many_members(w, django_assert_max_num_queries):
    for i in range(3):
        ending_in(w, 7, f"Seven {i}", f"97{5000 + i:08d}")
    with django_assert_max_num_queries(8) as few:
        queue_for(w.gym, w.today)
    for i in range(3, 15):
        ending_in(w, 7, f"Seven {i}", f"97{5000 + i:08d}")
    with django_assert_max_num_queries(len(few.captured_queries)):
        queue_for(w.gym, w.today + timedelta(days=1))
    assert Member.objects.filter(gym=w.gym).count() == 16
