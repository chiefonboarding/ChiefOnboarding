# Generated by Django 3.2.16 on 2023-05-06 21:55

import pyotp
from django.db import migrations, models
from django.utils.crypto import get_random_string


class Migration(migrations.Migration):
    def fix_empty_user_fields(apps, schema_editor):
        User = apps.get_model("users", "User")
        # manually looping through as we can't filter on empty totp_secret
        # due to encrypted field
        for user in User.objects.all():
            if (
                user.unique_url != ""
                and user.unique_url is not None
                and user.totp_secret != ""
            ):
                continue

            if user.unique_url == "" or user.unique_url is None:
                unique_string = get_random_string(length=8)
                while User.objects.filter(unique_url=unique_string).exists():
                    unique_string = get_random_string(length=8)

                user.unique_url = unique_string

            if user.totp_secret == "":
                user.totp_secret = pyotp.random_base32()

            user.save()

    dependencies = [
        ("users", "0031_alter_user_timezone"),
    ]

    operations = [
        migrations.RunPython(
            fix_empty_user_fields, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="user",
            name="unique_url",
            field=models.CharField(max_length=250, unique=True),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(("unique_url", ""), _negated=True),
                name="unique_url_not_empty",
            ),
        ),
    ]
