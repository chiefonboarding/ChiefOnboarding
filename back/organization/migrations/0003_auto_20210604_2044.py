# Generated by Django 3.1.8 on 2021-06-04 20:44

from django.db import migrations


class Migration(migrations.Migration):

    def load_schedules(apps, schema_editor):
        from django_q.models import Schedule
        Schedule.objects.create(func='sequences.tasks.timed_triggers', schedule_type=Schedule.HOURLY)
        Schedule.objects.create(func='slack_bot.tasks.first_day_reminder', schedule_type=Schedule.HOURLY)
        Schedule.objects.create(func='slack_bot.tasks.update_new_hire', schedule_type=Schedule.HOURLY)
        Schedule.objects.create(func='slack_bot.tasks.introduce_new_people', schedule_type=Schedule.HOURLY)
        Schedule.objects.create(func='slack_bot.tasks.link_slack_users', minutes=15, schedule_type=Schedule.MINUTES)
        Schedule.objects.create(func='integrations.tasks.create_accounts', minutes=15, schedule_type=Schedule.MINUTES)

    dependencies = [
        ('organization', '0002_auto_20201202_1505'),
    ]

    operations = [
        migrations.RunPython(load_schedules),
    ]
