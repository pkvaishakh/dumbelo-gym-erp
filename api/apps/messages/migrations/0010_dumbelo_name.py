"""Rackline is now Dumbelo. The owner's two messages change kind (`rackline_invoice_due` → `dumbelo_invoice_due`,
`rackline_payment_received` → `dumbelo_payment_received`) on templates, switches and messages already written, and
a receipt's dedupe key changes prefix (`rackline-receipt:` → `dumbelo-receipt:`) so it is still never sent twice.
"""
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Value
from django.db.models.functions import Concat, Substr

KINDS = {"rackline_invoice_due": "dumbelo_invoice_due", "rackline_payment_received": "dumbelo_payment_received"}


def rename(apps, kinds, old_prefix, new_prefix):
    for model in ("WhatsAppTemplate", "NotificationRule", "Message"):
        rows = apps.get_model("gym_messages", model).objects
        for old, new in kinds.items():
            rows.filter(kind=old).update(kind=new)
    apps.get_model("gym_messages", "Message").objects.filter(dedupe_key__startswith=old_prefix).update(
        dedupe_key=Concat(Value(new_prefix), Substr("dedupe_key", len(old_prefix) + 1)))


def forwards(apps, schema_editor):
    rename(apps, KINDS, "rackline-receipt:", "dumbelo-receipt:")


def backwards(apps, schema_editor):
    rename(apps, {new: old for old, new in KINDS.items()}, "dumbelo-receipt:", "rackline-receipt:")


class Migration(migrations.Migration):

    dependencies = [
        ('gym_messages', '0009_console_home_index'),
        ('gyms', '0005_dumbelo_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automationschedule',
            name='invoice_hour',
            field=models.PositiveSmallIntegerField(default=0, help_text="The hour on a gym's billing day its Dumbelo invoice is written", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)]),
        ),
        migrations.AlterField(
            model_name='message',
            name='billable',
            field=models.BooleanField(default=False, help_text="Sent from Dumbelo's shared number, so billed to the gym"),
        ),
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due'), ('payment_received', 'Payment received'), ('task_assigned', 'Task assigned'), ('dumbelo_invoice_due', 'Dumbelo invoice due'), ('dumbelo_payment_received', 'Dumbelo payment received')], max_length=32),
        ),
        migrations.AlterField(
            model_name='notificationrule',
            name='days_ahead',
            field=models.JSONField(blank=True, help_text="A plan ending soon: this gym's days in place of Dumbelo's", null=True),
        ),
        migrations.AlterField(
            model_name='notificationrule',
            name='hour',
            field=models.PositiveSmallIntegerField(blank=True, help_text="This gym's hour in place of Dumbelo's; empty means Dumbelo's", null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)]),
        ),
        migrations.AlterField(
            model_name='notificationrule',
            name='kind',
            field=models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due'), ('payment_received', 'Payment received'), ('task_assigned', 'Task assigned'), ('dumbelo_invoice_due', 'Dumbelo invoice due'), ('dumbelo_payment_received', 'Dumbelo payment received')], max_length=32),
        ),
        migrations.AlterField(
            model_name='whatsappaccount',
            name='gym',
            field=models.ForeignKey(blank=True, help_text="Empty for Dumbelo's shared number", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_accounts', to='gyms.gym'),
        ),
        migrations.AlterField(
            model_name='whatsapptemplate',
            name='kind',
            field=models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due'), ('payment_received', 'Payment received'), ('task_assigned', 'Task assigned'), ('dumbelo_invoice_due', 'Dumbelo invoice due'), ('dumbelo_payment_received', 'Dumbelo payment received')], max_length=32),
        ),
        migrations.RunPython(forwards, backwards),
    ]
