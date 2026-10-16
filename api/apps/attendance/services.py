"""One check-in rule book for the desk, the wall QR and the turnstile."""
from collections import defaultdict

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.gyms.models import GymRole

from .models import CheckIn, _token


def check_in(branch, *, member=None, staff=None, source, by=None, at=None):
    gym = branch.gym
    at = at or timezone.now()
    local = clock.local(gym, at)
    if not branch.is_active:
        raise RuleBroken("branch_closed", f"{branch.name} is not active")

    if member is not None:
        if member.gym_id != gym.id:
            raise RuleBroken("wrong_gym", "This member belongs to another gym")
        if member.is_archived:
            raise RuleBroken("member_archived", f"{member.name} is no longer a member")
        status = member.status(local.date())
        if status == "frozen":
            raise RuleBroken("membership_frozen", f"{member.name}'s plan is frozen")
        if status in ("expired", "none"):
            raise RuleBroken("membership_expired", f"{member.name}'s plan has ended. Renew it to check in.")
        earlier = CheckIn.objects.filter(member=member, local_date=local.date()).first()
        who = member.name
    else:
        if staff.gym_id != gym.id or not staff.is_active or staff.role not in GymRole.STAFF_ROLES:
            raise RuleBroken("not_staff", "Not active staff of this gym")
        if not staff.is_admin and not staff.branches.filter(pk=branch.pk).exists():
            raise RuleBroken("wrong_branch", f"{staff.user.name} doesn't work at {branch.name}")
        earlier = CheckIn.objects.filter(staff=staff, local_date=local.date()).first()
        who = staff.user.name

    if earlier:
        when = clock.time_label(gym, earlier.at)
        raise RuleBroken("already_checked_in", f"{who} already checked in today at {when}")
    try:
        with transaction.atomic():
            return CheckIn.objects.create(gym=gym, branch=branch, member=member, staff=staff, at=at, local_date=local.date(), source=source, recorded_by=by)
    except IntegrityError:  # two doors at the same second
        raise RuleBroken("already_checked_in", f"{who} already checked in today")


def session_name(checkin, gym):
    s = checkin.branch.session_for(clock.local(gym, checkin.at).time())
    return s.name if s else None


def count_by_session(checkins, gym):
    """Check-ins counted by session and by who came (member, trainer, receptionist, admin), sessions in the order
    of the day. Shared by the Attendance and Home screens. Returns (totals, sessions)."""
    from django.db.models import Min

    from apps.gyms.models import BranchSession

    zero = lambda: {"member": 0, "trainer": 0, "receptionist": 0, "admin": 0}  # noqa: E731
    totals, by_session = zero(), defaultdict(zero)
    for c in checkins:
        kind = "member" if c.member_id else c.staff.role
        by_session[session_name(c, gym) or "Other"][kind] += 1
        totals[kind] += 1
    # Morning before Evening: by the earliest start of a session with that name anywhere in the gym; "Other" last.
    starts = dict(BranchSession.objects.filter(branch__gym=gym).values("name").annotate(m=Min("starts")).values_list("name", "m"))
    order = sorted(by_session, key=lambda name: (name not in starts, starts.get(name) or name))
    return totals, [{"session": name, **by_session[name]} for name in order]


def rotate_device_token(device):
    """Give a turnstile a new token. The old one stops working at once, so it has to be set on the device."""
    device.token = _token()
    device.save(update_fields=["token", "updated_at"])
    return device


def deactivate_device(device):
    """Switch a turnstile off: its token is refused at the door. Devices are never deleted."""
    if not device.is_active:
        raise RuleBroken("already_off", "This device is already switched off")
    device.is_active = False
    device.save(update_fields=["is_active", "updated_at"])
    return device
