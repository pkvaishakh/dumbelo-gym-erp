"""Who needs a nudge today, and writing it down. Nothing here sends anything, and nothing here decides when:
the times are Dumbelo's (`apps.messages.automation`)."""
from collections.abc import Iterable
from datetime import date

from apps.members.models import Member

from .models import ReminderDue


def due_for(gym, for_date: date, days_ahead: Iterable[int] = ReminderDue.DAYS_AHEAD) -> list[tuple[Member, str, int | None]]:
    """The (member, kind, days left) the gym owes on this local day; days left only for a plan ending soon.

    Status comes from subscriptions, freezes and payments, so it is worked out in Python over the gym's members
    loaded with with_totals() — the same three queries the members list uses, and the same rules, so a reminder
    can never disagree with the badge on the screen. Fine to a few thousand members; a gym that outgrows it
    wants a stored status, which would serve both.
    """
    ahead = set(days_ahead)
    rows = []
    for member in Member.objects.filter(gym=gym, is_archived=False).with_totals():
        sub = member.current_subscription(for_date)
        if sub is None or sub.is_frozen(for_date):
            continue  # a paused plan isn't running out, and nothing is chased while it is paused
        left = (sub.ends - for_date).days
        if left == 0:
            rows.append((member, ReminderDue.PLAN_ENDS_TODAY, None))
        elif left in ahead:
            rows.append((member, ReminderDue.PLAN_ENDING, left))
        if member.balance_paise() > 0:
            rows.append((member, ReminderDue.PAYMENT_DUE, None))
    return rows


def queue_for(gym, for_date: date, days_ahead: Iterable[int] = ReminderDue.DAYS_AHEAD) -> int:
    """Write the gym's reminders for the day and say how many are new. Running it again adds nothing."""
    wanted = due_for(gym, for_date, days_ahead)
    already = set(ReminderDue.objects.filter(gym=gym, for_date=for_date).values_list("member_id", "kind"))
    fresh = [ReminderDue(gym=gym, member=m, kind=k, days_left=left, for_date=for_date) for m, k, left in wanted if (m.id, k) not in already]
    # ignore_conflicts as well as the check above: two runs at the same moment must not break on the constraint
    ReminderDue.objects.bulk_create(fresh, batch_size=500, ignore_conflicts=True)
    return len(fresh)
