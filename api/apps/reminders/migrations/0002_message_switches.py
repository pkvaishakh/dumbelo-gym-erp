"""Reminders take the messages' kinds, and a plan ending soon keeps how many days it had left, so the days
ahead can be set (gym_messages.AutomationSchedule) without a kind for each."""
from django.db import migrations, models


SIMPLE = {"expiring_0": "plan_ends_today", "dues": "payment_due"}


def forward(apps, schema_editor):
    ReminderDue = apps.get_model("reminders", "ReminderDue")
    for days in (7, 3):
        ReminderDue.objects.filter(kind=f"expiring_{days}").update(kind="plan_ending", days_left=days)
    for old, new in SIMPLE.items():
        ReminderDue.objects.filter(kind=old).update(kind=new)


def backward(apps, schema_editor):
    ReminderDue = apps.get_model("reminders", "ReminderDue")
    # Other days had no kind of their own before: the nearer of the two
    ReminderDue.objects.filter(kind="plan_ending", days_left__lte=3).update(kind="expiring_3")
    ReminderDue.objects.filter(kind="plan_ending").update(kind="expiring_7")
    for old, new in SIMPLE.items():
        ReminderDue.objects.filter(kind=new).update(kind=old)


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminderdue',
            name='days_left',
            field=models.PositiveSmallIntegerField(blank=True, help_text='For a plan ending soon: how many days it had left', null=True),
        ),
        migrations.AlterField(
            model_name='reminderdue',
            name='kind',
            field=models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due')], max_length=20),
        ),
        migrations.RunPython(forward, backward),
    ]
