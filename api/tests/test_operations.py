"""The restore drill's check (docs/operations.md): `manage.py verify_counts` counts what a gym has."""
import io
from datetime import timedelta

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from apps.attendance.models import CheckIn
from apps.core.money import rupees
from apps.gyms.models import Gym
from apps.members.models import Member, Payment
from apps.members.services import take_payment


def verify(*args) -> str:
    out = io.StringIO()
    call_command("verify_counts", *args, stdout=out)
    return out.getvalue()


def test_it_matches_the_seeded_demo_gym_and_counts_no_other(w):
    call_command("seed_demo", "--members", "12", stdout=io.StringIO())
    demo = Gym.objects.get(slug="rackline-fitness")
    payments = Payment.objects.filter(gym=demo)
    paid = sum(p.amount_paise for p in payments if not p.voided)

    lines = verify("--gym", "rackline-fitness").splitlines()

    assert lines[0] == "rackline-fitness  Rackline Fitness"
    assert lines[1].split()[:2] == ["members", "12"]
    assert lines[2].split()[:3] == ["payments", str(payments.count()), str(payments.filter(voided=True).count())]
    assert lines[2].endswith(f"{rupees(paid).removeprefix('₹')} rupees recorded")
    assert lines[3].split() == ["check-ins", str(CheckIn.objects.filter(gym=demo).count())]
    assert Member.objects.filter(gym=demo).count() == 12 and payments.exists() and CheckIn.objects.filter(gym=demo).exists()

    both = verify("--gym", "rackline-fitness", "--gym", w.gym.slug)
    assert f"{w.gym.slug}  {w.gym.name}\n  members           1   0 archived\n  payments          1   0 voided, 1,500 rupees recorded\n" in both


def test_until_counts_only_what_was_written_by_then(w):
    restore_point = timezone.now()
    later = w.new_member("Bina", "9800000099", w.a)
    Member.objects.filter(pk=later.pk).update(created_at=restore_point + timedelta(minutes=5))
    payment = Payment.objects.get(member=w.member)
    Payment.objects.filter(pk=payment.pk).update(voided=True, void_reason="Entered twice")
    take_payment(w.member, 500_00, "cash", by=w.desk)  # after the restore point, by the clock
    Payment.objects.filter(gym=w.gym).exclude(pk=payment.pk).update(created_at=restore_point + timedelta(minutes=6))

    out = verify("--gym", w.gym.slug, "--until", restore_point.isoformat())

    assert out.startswith(f"Rows written by {restore_point.isoformat()}\n")
    assert "  members           1   0 archived\n" in out
    assert "  payments          1   1 voided, 0 rupees recorded\n" in out  # voided since: counted, not in the money
    assert "  members           2" in verify("--gym", w.gym.slug)


def test_an_unknown_gym_or_a_bad_time_is_refused(w):
    with pytest.raises(CommandError, match="No gym with the short name nope"):
        verify("--gym", w.gym.slug, "--gym", "nope")
    with pytest.raises(CommandError, match="Give --until"):
        verify("--gym", w.gym.slug, "--until", "yesterday")
