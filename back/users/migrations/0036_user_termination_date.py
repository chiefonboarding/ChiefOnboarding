# Generated by Django 4.2.6 on 2023-10-27 00:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0035_integrationuser_user_integrations"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="termination_date",
            field=models.DateField(
                blank=True,
                help_text="Last day of working",
                null=True,
                verbose_name="Termination date",
            ),
        ),
    ]
