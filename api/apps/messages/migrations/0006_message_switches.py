"""Message switches and Rackline's schedule. Reminder messages take their template's kind (a plan ending soon says
how soon in its words), and a gym with reminders off gets its three reminders paused."""
import apps.messages.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


OLD_KINDS = {"expiring_7": "plan_ending", "expiring_3": "plan_ending", "expiring_0": "plan_ends_today", "dues": "payment_due"}
REMINDERS = ("plan_ending", "plan_ends_today", "payment_due")


def forward(apps, schema_editor):
    Message, Rule, Gym = apps.get_model("gym_messages", "Message"), apps.get_model("gym_messages", "NotificationRule"), apps.get_model("gyms", "Gym")
    for old, new in OLD_KINDS.items():
        Message.objects.filter(kind=old).update(kind=new)
    Rule.objects.bulk_create([
        Rule(gym_id=gym_id, kind=kind, is_on=False)
        for gym_id in Gym.objects.filter(reminders_on=False).values_list("id", flat=True) for kind in REMINDERS
    ])


def backward(apps, schema_editor):
    Message, Rule, Gym = apps.get_model("gym_messages", "Message"), apps.get_model("gym_messages", "NotificationRule"), apps.get_model("gyms", "Gym")
    paused = Rule.objects.filter(kind__in=REMINDERS, is_on=False).values_list("gym_id", flat=True)
    Gym.objects.filter(id__in=paused).update(reminders_on=False)
    # A plan ending soon was 7 or 3 days ahead before days could be set: the 3-day kind is the nearer guess
    Message.objects.filter(kind="plan_ending").update(kind="expiring_3")
    Message.objects.filter(kind="plan_ends_today").update(kind="expiring_0")
    Message.objects.filter(kind="payment_due").update(kind="dues")


class Migration(migrations.Migration):

    dependencies = [
        ('gym_messages', '0005_webhook'),
        ('gyms', '0003_gym_status_reason'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='kind',
            field=models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due'), ('payment_received', 'Payment received'), ('task_assigned', 'Task assigned'), ('rackline_invoice_due', 'Rackline invoice due'), ('rackline_payment_received', 'Rackline payment received')], max_length=32),
        ),
        migrations.CreateModel(
            name='AutomationSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reminder_hour', models.PositiveSmallIntegerField(default=6, help_text="The hour reminders go out, on each gym's clock", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)])),
                ('days_ahead', models.JSONField(default=apps.messages.models._days_ahead, help_text='How many days before a plan ends members are warned')),
                ('invoice_hour', models.PositiveSmallIntegerField(default=0, help_text="The hour on a gym's billing day its Rackline invoice is written", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)])),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('pk', 1)), name='one_automation_schedule')],
            },
        ),
        migrations.CreateModel(
            name='NotificationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('kind', models.CharField(choices=[('plan_ending', 'Plan ending soon'), ('plan_ends_today', 'Plan ends today'), ('payment_due', 'Payment due'), ('payment_received', 'Payment received'), ('task_assigned', 'Task assigned'), ('rackline_invoice_due', 'Rackline invoice due'), ('rackline_payment_received', 'Rackline payment received')], max_length=32)),
                ('is_on', models.BooleanField(default=True)),
                ('hour', models.PositiveSmallIntegerField(blank=True, help_text="This gym's hour in place of Rackline's; empty means Rackline's", null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)])),
                ('days_ahead', models.JSONField(blank=True, help_text="A plan ending soon: this gym's days in place of Rackline's", null=True)),
                ('gym', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gyms.gym')),
            ],
            options={
                'ordering': ['gym', 'kind'],
                'constraints': [models.UniqueConstraint(fields=('gym', 'kind'), name='one_rule_per_gym_message')],
            },
        ),
        migrations.RunPython(forward, backward),
    ]
