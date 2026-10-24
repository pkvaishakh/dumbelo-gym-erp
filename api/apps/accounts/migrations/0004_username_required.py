"""Every login has a username now (0003): it is required, unique and lowercase."""
from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_give_usernames"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(help_text="Lowercase letters, numbers, . and _; how they sign in", max_length=30, unique=True),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(condition=models.Q(username=Lower("username")), name="username_is_lowercase"),
        ),
    ]
