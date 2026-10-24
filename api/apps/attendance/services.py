"""One check-in rule book for the desk, the wall QR and the turnstile."""
from collections import defaultdict
from datetime import UTC, datetime, time

from django.db import IntegrityError, transaction
from django.db.models import Count, Min
from django.db.models.functions import ExtractHour, ExtractMinute
from django.utils import timezone

from apps.core import clock
from apps.core.errors import RuleBroken
from apps.core.tenancy import gym_suspended
from apps.gyms.models import Branch, BranchSession, GymRole

from .models import CheckIn, _token


def check_in(branch, *, member=None, staff=None, source, by=None, at=None):
    gym = branch.gym
    at = at or timezone.now()
    local = clock.local(gym, at)
    if gym.is_suspended:  # the wall QR and the turnstile don't come through InGym
        raise gym_suspended()
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
        if status == "none" and gym.pt_needs_membership and member.subscriptions.filter(cancelled=False).exists():
            raise RuleBroken("membership_expired", f"{member.name} has personal training but no membership. Sell them one to check in.")
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


def change_time(checkin, new_time: time, *, now=None):
    """Move a check-in to another time on the same day, e.g. a turnstile whose clock was off. Its day never changes,
    so the one-per-day rule still holds; its session follows the new time."""
    at = datetime.combine(checkin.local_date, new_time, tzinfo=clock.tz(checkin.gym)).astimezone(UTC)  # stored UTC, as every time is
    if at > (now or timezone.now()):
        raise RuleBroken("time_in_future", "Pick a time that has already passed")
    checkin.at = at
    checkin.save(update_fields=["at", "updated_at"])
    return checkin


def session_name(checkin, gym):
    s = checkin.branch.session_for(clock.local(gym, checkin.at).time())
    return s.name if s else None


def _tally(rows, gym):
    """(session, who came, how many) rows into totals and sessions in the order of the day: Morning before Evening,
    by the earliest start of a session with that name anywhere in the gym, and "Other" last."""
    zero = lambda: {"member": 0, "trainer": 0, "receptionist": 0, "admin": 0}  # noqa: E731
    totals, by_session = zero(), defaultdict(zero)
    for name, kind, n in rows:
        by_session[name][kind] += n
        totals[kind] += n
    starts = dict(BranchSession.objects.filter(branch__gym=gym).values("name").annotate(m=Min("starts")).values_list("name", "m"))
    order = sorted(by_session, key=lambda name: (name not in starts, starts.get(name) or name))
    return totals, [{"session": name, **by_session[name]} for name in order]


def count_by_session(checkins, gym):
    """Check-ins counted by session and by who came (member, trainer, receptionist, admin), sessions in the order
    of the day. Shared by the Attendance and Home screens. Returns (totals, sessions)."""
    return _tally(((session_name(c, gym) or "Other", "member" if c.member_id else c.staff.role, 1) for c in checkins), gym)


def count_by_session_over(checkins, gym):
    """The same counts as `count_by_session` for any number of days, without loading each check-in: grouped by
    branch, local time to the minute and who came, so the work grows with the minutes in a day, not the visits."""
    zone = clock.tz(gym)
    rows = (checkins.order_by().annotate(h=ExtractHour("at", tzinfo=zone), m=ExtractMinute("at", tzinfo=zone))
            .values_list("branch_id", "h", "m", "staff__role").annotate(n=Count("id")))
    branches = {b.pk: b for b in Branch.objects.filter(gym=gym).prefetch_related("sessions")}

    def name(branch_id, h, m):
        s = branches[branch_id].session_for(time(h, m))
        return s.name if s else "Other"

    return _tally(((name(b, h, m), role or "member", n) for b, h, m, role, n in rows), gym)


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
