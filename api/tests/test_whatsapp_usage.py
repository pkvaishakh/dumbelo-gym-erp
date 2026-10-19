"""Usage on Rackline's shared number: the gym's own billing month so far, and every gym's month in the Console."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from apps.billing.services import change_plan
from apps.messages.models import Message
from tests.test_gym_message_log import message
from tests.test_platform import rackline, support

USAGE = "/api/messages/usage/"
CONSOLE = "/api/platform/whatsapp-usage/"
INDIA = ZoneInfo("Asia/Kolkata")


def delivered(w, n, at, rate=15, billable=True):
    return message(w, n, billable=billable, rate_paise=rate, delivered_at=at)


def local(day, hour=12, zone=INDIA):
    return datetime.combine(day, datetime.min.time(), zone).replace(hour=hour)


# ---- The gym's own ----

def test_the_gym_sees_its_billing_month_so_far_and_when_its_billed(w):
    change_plan(w.gym, billing_day=5)
    starts = w.today.replace(day=5) if w.today.day >= 5 else (w.today.replace(day=1) - timedelta(days=1)).replace(day=5)
    for n in range(3):
        delivered(w, n, local(starts))
    delivered(w, 7, local(starts, hour=23), rate=90)
    delivered(w, 8, local(starts - timedelta(days=1)))  # last billing month: already on an invoice
    delivered(w, 9, local(starts), billable=False)  # from a gym's own number: Meta bills the gym

    r = w.client(w.admin).get(USAGE)

    assert r.status_code == 200, r.content
    body = r.json()
    assert body["mode"] == "shared" and body["starts"] == starts.isoformat()
    assert date.fromisoformat(body["billed_on"]).day == 5 and date.fromisoformat(body["billed_on"]) > w.today
    assert body["messages"] == 4 and body["amount_paise"] == 3 * 15 + 90
    assert [(line["rate_paise"], line["messages"]) for line in body["lines"]] == [(15, 3), (90, 1)]


def test_only_the_gyms_admins_see_what_its_messages_cost(w, other):
    delivered(other, 1, local(other.today))
    assert w.client(w.admin).get(USAGE).json()["messages"] == 0
    for c in (w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(USAGE).status_code == 403


# ---- The Console's: every gym, one month ----

def test_the_console_lists_each_gyms_month_biggest_first_with_totals(w, other, django_assert_max_num_queries):
    month = date(2026, 9, 1)
    for n in range(2):
        delivered(w, n, local(month + timedelta(days=n)))
    for n in range(3):
        delivered(other, n, local(month + timedelta(days=10)), rate=90)
    delivered(w, 9, local(month - timedelta(days=1)))  # August

    console = rackline()
    with django_assert_max_num_queries(4):  # the time zones, the gyms' count and page, the month's totals
        r = console.get(CONSOLE, {"month": "2026-09"})

    assert r.status_code == 200, r.content
    body = r.json()
    assert body["month"] == "2026-09" and body["messages"] == 5 and body["amount_paise"] == 2 * 15 + 3 * 90 and body["count"] == 2
    assert [(row["gym_name"], row["messages"], row["amount_paise"]) for row in body["results"]] == [
        (other.gym.name, 3, 270), (w.gym.name, 2, 30),
    ]
    assert w.member.name not in r.content.decode()


def test_a_month_is_each_gyms_own_as_its_invoice_counts_it(w, other):
    """1 Oct, 1 AM in India is still 30 Sep in Dubai: India's gym counts it in October, Dubai's in September."""
    other.gym.timezone = "Asia/Dubai"
    other.gym.save()
    at = datetime(2026, 10, 1, 1, 0, tzinfo=INDIA)
    delivered(w, 1, at)
    delivered(other, 1, at)

    console = rackline()
    october = console.get(CONSOLE, {"month": "2026-10"}).json()
    september = console.get(CONSOLE, {"month": "2026-09"}).json()
    assert [row["gym"] for row in october["results"]] == [w.gym.pk]
    assert [row["gym"] for row in september["results"]] == [other.gym.pk]


def test_the_console_pages_the_gyms(w, other):
    for world in (w, other):
        delivered(world, 1, local(world.today))
    first = rackline().get(CONSOLE, {"limit": 1}).json()
    assert first["count"] == 2 and len(first["results"]) == 1 and first["next"]
    assert Message.objects.filter(billable=True).count() == 2


def test_a_bad_month_says_how_to_write_it(w):
    console = rackline()
    for bad in ("2026-13", "Sept", "2026-9"):
        r = console.get(CONSOLE, {"month": bad})
        assert r.status_code == 400 and "month" in r.json()["error"]["fields"], bad


def test_only_rackline_admins_see_every_gyms_usage(w):
    for c in (support(), w.client(w.admin), w.client(w.desk)):
        assert c.get(CONSOLE).status_code == 403
