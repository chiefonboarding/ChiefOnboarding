# Generated by Django 3.2.10 on 2022-02-09 21:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0018_auto_20220209_2138"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="department",
        ),
    ]