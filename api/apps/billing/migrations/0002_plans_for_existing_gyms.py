"""Every gym already on Rackline gets its Rackline plan, with room for the branches it has open.

Their prices come from a starting price list at zero, made here only when there are gyms and no list yet: a
Rackline admin adds the real prices in the Console and moves each gym to them.
"""
from datetime import date
from zoneinfo import ZoneInfo

from django.db import migrations


def plans_for_gyms(apps, schema_editor):
    Gym = apps.get_model("gyms", "Gym")
    Branch = apps.get_model("gyms", "Branch")
    PriceList = apps.get_model("billing", "PriceList")
    GymBilling = apps.get_model("billing", "GymBilling")
    gyms = list(Gym.objects.filter(billing__isnull=True))
    if not gyms:
        return
    prices = PriceList.objects.order_by("-active_from").first()
    if prices is None:
        prices = PriceList.objects.create(
            active_from=date(2026, 1, 1), base_paise=0, per_branch_paise=0, whatsapp_setup_paise=0, machine_setup_paise=0,
            utility_message_paise=0, marketing_message_paise=0, authentication_message_paise=0,
            note="Starting prices, before Rackline set its own",
        )
    copied = {f: getattr(prices, f) for f in (
        "base_paise", "per_branch_paise", "whatsapp_setup_paise", "machine_setup_paise", "utility_message_paise",
        "marketing_message_paise", "authentication_message_paise",
    )}
    rows = []
    for gym in gyms:
        open_now = Branch.objects.filter(gym=gym, is_active=True).count()
        joined = gym.created_at.astimezone(ZoneInfo(gym.timezone or "Asia/Kolkata")).day
        rows.append(GymBilling(gym=gym, price_list=prices, branch_quota=max(open_now, 1), billing_day=min(joined, 28),
                               whatsapp_mode="shared", **copied))
    GymBilling.objects.bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        ("gyms", "0003_gym_status_reason"),
    ]

    operations = [migrations.RunPython(plans_for_gyms, migrations.RunPython.noop)]
