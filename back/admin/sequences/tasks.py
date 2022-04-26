from django.contrib.auth import get_user_model
from django_q.tasks import async_task

from admin.sequences.models import Condition


def process_condition(condition, user):
    """
    Processing triggered condition

    :param Condition condition: the condition that got triggered
    :param User user: the user that it got triggered for
    """

    condition.proces_condition(user)


def timed_triggers():
    """
    This gets triggered every 5 minutes to trigger conditions within sequences.
    These conditions are already assigned to new hires.
    """

    for user in get_user_model().new_hires.all():

        amount_days = user.workday
        amount_days_before = user.days_before_starting
        current_time = user.get_local_time().time()

        # Get conditions before/after they started
        # Generally, this should be only one, but just in case, we can handle more
        conditions = Condition.objects.none()
        if amount_days == 0:
            conditions = user.conditions.filter(
                condition_type=2, days=amount_days_before, current_time=current_time
            )
        elif user.get_local_time().weekday() < 5:
            conditions = user.conditions.filter(condition_type=0, days=amount_days)

        # Schedule conditions to be executed with new scheduled task, we do this to
        # avoid long standing tasks. I.e. sending lots of emails might take more time.
        for i in conditions:
            async_task(i.process_condition(user))
