"""The Console's gyms as its screens read them: the list, a gym's screen and Home all start from `gyms()`."""
import django_filters
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from django.utils import timezone

from apps.billing.invoicing import overdue_by_gym, owed_by_gym
from apps.core.queries import count_of
from apps.gyms.models import Branch, Gym, GymRole
from apps.members.models import Member


def gyms():
    """Gyms with their counts, owner and what they owe Dumbelo, a fixed number of queries whatever the page size."""
    owner = GymRole.objects.filter(gym=OuterRef("pk"), is_owner=True).select_related("user")
    return Gym.objects.annotate(
        branch_count=count_of(Branch.objects.filter(gym=OuterRef("pk"), is_active=True)),
        member_count=count_of(Member.objects.filter(gym=OuterRef("pk"), is_archived=False)),
        owner_name=Subquery(owner.values("user__name")[:1]),
        owner_email=Subquery(owner.values("user__email")[:1]),
        owed_paise=owed_by_gym(),
    )


def with_branches(qs):
    """The gym's branches as `branch_rows`, each with its member count: two queries for the gym's screen."""
    members = Count("members", filter=Q(members__is_archived=False))
    return qs.prefetch_related(Prefetch("branches", Branch.objects.annotate(member_count=members).order_by("name"), to_attr="branch_rows"))


class GymFilter(django_filters.FilterSet):
    """`?status=` and `?owes=`: Home's money figures open the list with the gyms they count."""

    ANY, OVERDUE = "any", "overdue"
    owes = django_filters.ChoiceFilter(choices=[(ANY, "Owes Dumbelo anything"), (OVERDUE, "Has an invoice past its due day")],
                                       method="filter_owes")

    class Meta:
        model = Gym
        fields = ["status"]

    def filter_owes(self, qs, name, value):
        if value == self.OVERDUE:  # Dumbelo's day, as on the invoices
            return qs.annotate(overdue_paise=overdue_by_gym(timezone.localdate())).filter(overdue_paise__gt=0)
        return qs.filter(owed_paise__gt=0)
