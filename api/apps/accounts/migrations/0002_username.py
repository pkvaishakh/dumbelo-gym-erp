"""Everyone signs in with a username (filled in by 0003). Email and phone stop being unique: they become contact
details that several logins may share, like a family's phone."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="user", name="user_has_email_or_phone"),
        migrations.AlterField(model_name="user", name="email", field=models.EmailField(blank=True, max_length=254, null=True)),
        migrations.AlterField(
            model_name="user", name="phone", field=models.CharField(blank=True, db_index=True, max_length=13, null=True),
        ),
        migrations.AddField(model_name="user", name="username", field=models.CharField(max_length=30, null=True)),
    ]
