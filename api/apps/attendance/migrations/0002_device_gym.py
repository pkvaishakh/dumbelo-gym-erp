# A device now carries its gym, like every other gym-owned row, so a serial only has to be unique inside
# one gym: two gyms may own the same model of reader with the same number on the box.
import django.db.models.deletion
from django.db import migrations, models


def set_gym_from_branch(apps, schema_editor):
    """Every device already sits at a branch, and every branch belongs to a gym: copy it across."""
    Device = apps.get_model("attendance", "Device")
    devices = list(Device.objects.select_related("branch"))
    for device in devices:
        device.gym_id = device.branch.gym_id
    Device.objects.bulk_update(devices, ["gym"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("attendance", "0001_initial"), ("gyms", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="device",
            name="gym",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="gyms.gym"),
        ),
        migrations.RunPython(set_gym_from_branch, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="device",
            name="gym",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="gyms.gym"),
        ),
        migrations.AlterField(model_name="device", name="serial", field=models.CharField(max_length=60)),
        migrations.AddConstraint(
            model_name="device",
            constraint=models.UniqueConstraint(fields=("gym", "serial"), name="device_serial_unique_in_gym"),
        ),
    ]
