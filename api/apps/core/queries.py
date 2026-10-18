"""Query pieces two or more apps use."""
from django.db.models import F, Func, IntegerField, Subquery, Value
from django.db.models.functions import Coalesce


def count_of(qs):
    """How many rows of `qs` (filtered on OuterRef) belong to each outer row, as one subquery. COUNT as a plain
    function, so Django adds no GROUP BY and the subquery always answers one row."""
    counted = qs.order_by().annotate(n=Func(F("pk"), function="COUNT")).values("n")
    return Coalesce(Subquery(counted, output_field=IntegerField()), Value(0))


def sum_of(qs, field):
    """The total of `field` over the rows of `qs` (filtered on OuterRef) for each outer row, 0 when there are none.
    One subquery, like `count_of`."""
    summed = qs.order_by().annotate(t=Func(F(field), function="SUM")).values("t")
    return Coalesce(Subquery(summed, output_field=IntegerField()), Value(0))
