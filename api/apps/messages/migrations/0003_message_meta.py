"""Messages grow what sending through Meta needs: the number and template they went on, a key that stops them going
twice, and Meta's side of things. Rows already there were reminders, each tried once, so their key is the reminder's.
The key is filled here and made required (and unique) in 0004, so no table is altered after it was updated in the
same transaction (Postgres refuses that)."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import CharField, Value
from django.db.models.functions import Cast, Concat


def fill_keys(apps, schema_editor):
    Message = apps.get_model("gym_messages", "Message")
    # One UPDATE for every row: a date cast to text is YYYY-MM-DD on both Postgres and SQLite.
    Message.objects.update(
        dedupe_key=Concat(Value("member:"), Cast("member_id", CharField()), Value(":reminder:"), Cast("for_date", CharField())),
        attempts=1,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("gym_messages", "0002_whatsapp_accounts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="message", name="one_message_per_member_per_day"),
        migrations.AlterField(
            model_name="message",
            name="member",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="members.member"),
        ),
        migrations.AddField(
            model_name="message",
            name="user",
            field=models.ForeignKey(blank=True, help_text="A staff member it went to; empty when it went to a member", null=True,
                                    on_delete=django.db.models.deletion.CASCADE, related_name="+", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="message",
            name="kind",
            field=models.CharField(choices=[
                ("expiring_7", "Plan ends in 7 days"), ("expiring_3", "Plan ends in 3 days"), ("expiring_0", "Plan ends today"),
                ("dues", "Payment due"), ("payment_received", "Payment received"), ("task_assigned", "Task assigned"),
                ("rackline_invoice_due", "Rackline invoice due"), ("rackline_payment_received", "Rackline payment received"),
            ], max_length=32),
        ),
        migrations.AddField(
            model_name="message",
            name="dedupe_key",
            field=models.CharField(help_text="Unique in the gym: the same message is never sent twice", max_length=80, null=True),
        ),
        migrations.AddField(
            model_name="message",
            name="account",
            field=models.ForeignKey(blank=True, help_text="The number it went from; empty when there was none to send from", null=True,
                                    on_delete=django.db.models.deletion.RESTRICT, related_name="messages", to="gym_messages.whatsappaccount"),
        ),
        migrations.AddField(
            model_name="message",
            name="template",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name="messages",
                                    to="gym_messages.whatsapptemplate"),
        ),
        migrations.AddField(
            model_name="message",
            name="parameters",
            field=models.JSONField(default=list, help_text="What filled the template's {{1}}, {{2}}…, in order"),
        ),
        migrations.AlterField(
            model_name="message",
            name="text",
            field=models.TextField(help_text="The template's words, filled in"),
        ),
        migrations.AlterField(
            model_name="message",
            name="for_date",
            field=models.DateField(help_text="The day in the gym's time zone it was for"),
        ),
        migrations.AlterField(
            model_name="message",
            name="status",
            field=models.CharField(choices=[("queued", "Sending"), ("sent", "Sent"), ("delivered", "Delivered"), ("read", "Read"),
                                            ("failed", "Failed")], default="queued", max_length=10),
        ),
        migrations.AddField(
            model_name="message",
            name="attempts",
            field=models.PositiveSmallIntegerField(default=0, help_text="Times it was handed to the provider"),
        ),
        migrations.AddField(
            model_name="message",
            name="next_retry_at",
            field=models.DateTimeField(blank=True, help_text="When a temporary failure is tried again", null=True),
        ),
        migrations.AlterField(
            model_name="message",
            name="provider_id",
            field=models.CharField(blank=True, help_text="The provider's own id for the message", max_length=128),
        ),
        migrations.AddField(
            model_name="message",
            name="error_code",
            field=models.CharField(blank=True, help_text="Meta's error code, when it gave one", max_length=16),
        ),
        migrations.AddField(
            model_name="message",
            name="billable",
            field=models.BooleanField(default=False, help_text="Sent from Rackline's shared number, so billed to the gym"),
        ),
        migrations.AddField(
            model_name="message",
            name="rate_paise",
            field=models.PositiveIntegerField(default=0, help_text="What it costs the gym once delivered"),
        ),
        migrations.RunPython(fill_keys, migrations.RunPython.noop),
    ]
