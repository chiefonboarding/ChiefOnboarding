from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.sequences.emails import send_sequence_update_message
from admin.sequences.models import Condition
from organization.models import Notification, Organization
from slack_bot.slack_intro import SlackIntro
from slack_bot.slack_resource import SlackResource
from slack_bot.slack_to_do import SlackToDo
from slack_bot.utils import Slack, paragraph
from users.models import ResourceUser, ToDoUser


def process_condition(condition_id, user_id):
    """
    Processing triggered condition

    :param Condition condition: the condition that got triggered
    :param User user: the user that it got triggered for
    """

    condition = Condition.objects.get(id=condition_id)
    user = get_user_model().objects.get(id=user_id)
    condition.process_condition(user)

    # Send notifications to user
    notifications = Notification.objects.filter(
        notification_type__in=[
            "added_todo",
            "added_resource",
            "added_badge",
            "added_introduction",
        ],
        created_for=user,
        notified_user=False,
    )

    if not notifications.exists():
        return

    if user.has_slack_account:
        to_do_blocks = [
            SlackToDo(
                ToDoUser.objects.get(to_do__id=notif.item.id, user=user), user
            ).to_do_block()
            for notif in notifications.filter(notification_type="added_todo")
        ]

        resource_blocks = [
            SlackResource(
                ResourceUser.objects.get(user=user, resource__id=notif.id), user
            ).get_block()
            for notif in notifications.filter(notification_type="added_resource")
        ]

        badge_blocks = [
            paragraph(
                _("*Congrats, you unlocked: %(item_name)s *\n %(message)s")
                % {
                    "item_name": user.personalize(
                        Badge.objects.get(id=notif.item_id).name
                    ),
                    "message": Badge.objects.get(id=notif.item_id).to_slack_block(user),
                }
            )
            for notif in notifications.filter(notification_type="added_badge")
        ]

        intro_blocks = [
            SlackIntro(Introduction.objects.get(id=notif.item_id), user).format_block()
            for notif in notifications.filter(notification_type="added_introduction")
        ]

        Slack().send_message(
            text=_("Here are some new items for you!"),
            blocks=[
                paragraph(_("Here are some new items for you!")),
                *intro_blocks,
                *badge_blocks,
                *resource_blocks,
                *to_do_blocks,
            ],
            channel=user.slack_user_id,
        )
    else:
        send_sequence_update_message(notifications, user)

    # Update notifications to not notify user again
    notifications.update(notified_user=True)

    # Update user amount completed
    user.update_progress()


def timed_triggers():
    """
    This gets triggered every 5 minutes to trigger conditions within sequences.
    These conditions are already assigned to new hires.
    """
    org = Organization.object.get()

    current_datetime = timezone.now()
    last_updated = org.timed_triggers_last_check

    # Round downwards (based on 5 minutes) - check if we might not be on 5/0 anymore.
    # A time of 16 minutes becomes 15
    off_by_minutes = current_datetime.minute % 5
    current_datetime = current_datetime.replace(
        minute=current_datetime.minute - off_by_minutes, second=0, microsecond=0
    )

    # Same for last_updated (though, this should always be rounded on 5 or 0 already)
    off_by_minutes = last_updated.minute % 5
    last_updated = last_updated.replace(
        minute=last_updated.minute - off_by_minutes, second=0, microsecond=0
    )

    # Generally this loop will only go through once. In the case of an outage, it will
    # walk through all the 5 minutes that it needs to catch up on based on the last
    # updated variable
    while current_datetime > last_updated:
        last_updated += timedelta(minutes=5)
        org.timed_triggers_last_check = last_updated
        org.save()

        for user in get_user_model().new_hires.all():

            amount_days = user.workday
            amount_days_before = user.days_before_starting
            current_time = user.get_local_time(last_updated).time()

            # Get conditions before/after they started
            # Generally, this should be only one, but just in case, we can handle more
            conditions = Condition.objects.none()
            if amount_days == 0:
                conditions = user.conditions.filter(
                    condition_type=2, days=amount_days_before, current_time=current_time
                )
            elif user.get_local_time(last_updated).weekday() < 5:
                conditions = user.conditions.filter(condition_type=0, days=amount_days)

            # Schedule conditions to be executed with new scheduled task, we do this to
            # avoid long standing tasks. I.e. sending lots of emails might take more
            # time.
            for i in conditions:
                async_task(process_condition, i.id, user.id)
