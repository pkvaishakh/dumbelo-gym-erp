from django.db import migrations
from django.db.models import OuterRef, Subquery


def sessions_from_plans(apps, schema_editor):
    """Personal training already sold keeps the sessions its plan had, and the member's trainer as its trainer.
    PT plans without a length ran 3 months (clock.plan_end's fallback), so they get that length now."""
    Plan = apps.get_model("members", "Plan")
    Subscription = apps.get_model("members", "Subscription")
    Plan.objects.filter(kind="pt", months=0).update(months=3)
    pt = Subscription.objects.filter(plan__kind="pt")
    pt.update(sessions=Subquery(Plan.objects.filter(pk=OuterRef("plan_id")).values("sessions")[:1]))
    for sub in pt.filter(trainer__isnull=True, member__trainer__isnull=False).select_related("member").iterator():
        Subscription.objects.filter(pk=sub.pk).update(trainer_id=sub.member.trainer_id)


class Migration(migrations.Migration):
    """Apart from 0009: Postgres won't build that one's indexes in a transaction that has just updated rows."""

    dependencies = [("members", "0009_pt_sessions")]

    operations = [migrations.RunPython(sessions_from_plans, migrations.RunPython.noop)]
