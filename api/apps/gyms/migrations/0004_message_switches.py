"""`reminders_on` goes: each message has its own switch now (gym_messages.NotificationRule, which carried it over)."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gyms', '0003_gym_status_reason'),
        ('gym_messages', '0006_message_switches'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gym',
            name='reminders_on',
        ),
    ]
