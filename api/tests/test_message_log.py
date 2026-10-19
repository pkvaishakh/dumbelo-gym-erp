"""Console → WhatsApp log: every message sent across gyms, with search and filters, and nothing a gym keeps to itself."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.messages.models import Message, WhatsAppAccount, WhatsAppTemplate
from tests.test_platform import dumbelo, support

LOG = "/api/platform/messages/"
INDIA = ZoneInfo("Asia/Kolkata")


def sent(w, account, n, *, status=Message.DELIVERED, kind="plan_ending", to=None, at=None, **extra):
    template = WhatsAppTemplate.objects.filter(account=account, kind=kind).first()
    m = Message.objects.create(gym=w.gym, member=w.member, kind=kind, dedupe_key=f"log:{w.gym.slug}:{n}", to=to or w.member.phone,
                               text=f"Hi {w.member.name}, your plan ends soon", parameters=[w.member.name], for_date=w.today,
                               provider="whatsapp_cloud", status=status, account=account, template=template, **extra)
    if at:
        Message.objects.filter(pk=m.pk).update(created_at=at)
    return m


def own_number(w):
    account = WhatsAppAccount(gym=w.gym, waba_id="100000000000002", phone_number_id="200000000000002", display_number="+91 80000 00002")
    account.set_credentials(access_token="EAAGown-number-token-1111111111", app_secret="own-number-app-secret-11")
    account.save()
    WhatsAppTemplate.objects.create(account=account, kind="plan_ending", name="iron_plan_ending", body="Hi {{1}}", parameters=["first_name"],
                                    status=WhatsAppTemplate.APPROVED)
    return account


def ids(r):
    assert r.status_code == 200, r.content
    return [m["id"] for m in r.json()["results"]]


def test_only_dumbelo_admins_see_the_log(w, shared_number):
    sent(w, shared_number, 1)
    for c in (support(), w.client(w.admin), w.client(w.desk), w.client(w.trainer), w.member_client()):
        assert c.get(LOG).status_code == 403


def test_the_log_shows_how_each_message_went_but_never_who_or_what(w, other, shared_number, django_assert_max_num_queries):
    own = own_number(w)
    for n in range(6):
        sent(w, own if n % 2 else shared_number, n)
        sent(other, shared_number, n, status=Message.FAILED, error="Message undeliverable (code 131026)", error_code="131026")

    with django_assert_max_num_queries(3):
        r = dumbelo().get(LOG)

    body = r.json()
    assert body["count"] == 12 and len({m["gym"] for m in body["results"]}) == 2
    row = next(m for m in body["results"] if m["account"] == own.pk)
    assert row["gym_name"] == w.gym.name and row["account_number"] == "+91 80000 00002" and row["is_shared"] is False
    assert row["template_name"] == "iron_plan_ending" and row["kind_label"] == "Plan ending soon" and row["status"] == "delivered"
    assert row["recipient"] == "member" and row["to_last4"] == w.member.phone[-4:]
    text = r.content.decode()
    assert w.member.name not in text and other.member.name not in text and "your plan ends" not in text
    assert w.member.phone not in text and "token" not in text and "secret" not in text
    assert "to" not in row and "text" not in row and "parameters" not in row


def test_filters_by_gym_number_template_message_and_status(w, other, shared_number):
    own = own_number(w)
    mine = sent(w, own, 1)
    shared = sent(w, shared_number, 2, status=Message.FAILED)
    theirs = sent(other, shared_number, 3, kind="payment_due")
    ops = dumbelo()

    assert ids(ops.get(LOG, {"gym": other.gym.pk})) == [theirs.pk]
    assert ids(ops.get(LOG, {"account": own.pk})) == [mine.pk]
    assert set(ids(ops.get(LOG, {"account": shared_number.pk}))) == {shared.pk, theirs.pk}
    assert ids(ops.get(LOG, {"template": mine.template_id})) == [mine.pk]
    assert ids(ops.get(LOG, {"kind": "payment_due"})) == [theirs.pk]
    assert ids(ops.get(LOG, {"status": "failed", "gym": w.gym.pk})) == [shared.pk]
    assert ops.get(LOG, {"gym": "abc"}).status_code == 400
    assert ops.get(LOG, {"status": "lost"}).status_code == 400


def test_search_by_number_meta_id_or_error(w, other, shared_number):
    by_number = sent(w, shared_number, 1, to="+919811112222")
    by_meta = sent(w, shared_number, 2, provider_id="wamid.HBgMOTE5ODAwMDAwMDAx")
    by_error = sent(other, shared_number, 3, status=Message.FAILED, error="Re-engagement message (code 131047)", error_code="131047")
    ops = dumbelo()

    assert ids(ops.get(LOG, {"q": "2222"})) == [by_number.pk]
    assert ids(ops.get(LOG, {"q": "+91 98111 12222"})) == [by_number.pk]  # a whole number, typed as people write it
    assert ids(ops.get(LOG, {"q": "HBgMOTE5"})) == [by_meta.pk]
    assert ids(ops.get(LOG, {"q": "131047"})) == [by_error.pk]
    assert ids(ops.get(LOG, {"q": "re-engagement"})) == [by_error.pk]
    assert len(ids(ops.get(LOG, {"q": "2"}))) == 3  # under 2 characters: no search


def test_days_are_dumbelo_days_and_a_backwards_span_is_refused(w, shared_number):
    morning = sent(w, shared_number, 1, at=datetime(2026, 10, 18, 0, 30, tzinfo=INDIA))  # 17 Oct in UTC, 18 Oct in India
    late = sent(w, shared_number, 2, at=datetime(2026, 10, 18, 23, 50, tzinfo=INDIA))
    sent(w, shared_number, 3, at=datetime(2026, 10, 19, 0, 10, tzinfo=INDIA))
    ops = dumbelo()

    assert set(ids(ops.get(LOG, {"from": "2026-10-18", "to": "2026-10-18"}))) == {morning.pk, late.pk}
    assert len(ids(ops.get(LOG, {"from": "2026-10-19"}))) == 1
    r = ops.get(LOG, {"from": "2026-10-19", "to": "2026-10-18"})
    assert r.status_code == 400 and "from" in r.json()["error"]["fields"]
    assert ops.get(LOG, {"from": "18-10-2026"}).status_code == 400


def test_newest_first(w, shared_number):
    now = timezone.now()
    old = sent(w, shared_number, 1, at=now - timedelta(days=1))
    new = sent(w, shared_number, 2, at=now)
    assert ids(dumbelo().get(LOG)) == [new.pk, old.pk]
