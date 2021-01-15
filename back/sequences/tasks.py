from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth import get_user_model
from django.utils import translation
from slack_bot.slack import Slack

from .emails import send_sequence_update_message
from .models import Condition
from sequences.models import Condition


@periodic_task(run_every=(crontab(minute='0')), name="timed_triggers", ignore_result=True)
def timed_triggers():
    for user in get_user_model().objects.filter(role=0):
        # make sure it's 8 AM for the new hire
        if user.get_local_time().hour == 8:
            translation.activate(user.language)
            amount_days = user.workday()
            amount_days_before = user.days_before_starting()
            # check if it's before or after they start
            conditions = []
            if amount_days == 0:
                conditions = user.conditions.filter(condition_type=2, days=amount_days_before)
            elif user.get_local_time().weekday() < 5:
                conditions = user.conditions.filter(condition_type=0, days=amount_days)
            # process conditions and send it through Slack/email
            for i in conditions:
                items = i.process_condition(user)
                if user.slack_user_id is not None:
                    s = Slack()
                    s.set_user(user)
                    s.send_sequence_triggers(items, None)
                else:
                    send_sequence_update_message(user, items)

    return
