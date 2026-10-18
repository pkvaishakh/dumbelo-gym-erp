from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gym_messages", "0003_message_meta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="dedupe_key",
            field=models.CharField(help_text="Unique in the gym: the same message is never sent twice", max_length=80),
        ),
        migrations.AddConstraint(
            model_name="message",
            constraint=models.UniqueConstraint(fields=("gym", "dedupe_key"), name="one_message_per_key"),
        ),
        migrations.AddConstraint(
            model_name="message",
            constraint=models.CheckConstraint(
                condition=models.Q(models.Q(("member__isnull", False), ("user__isnull", True)),
                                   models.Q(("member__isnull", True), ("user__isnull", False)), _connector="OR"),
                name="message_to_a_member_or_a_user",
            ),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["status", "next_retry_at"], name="message_retry_due"),
        ),
    ]
