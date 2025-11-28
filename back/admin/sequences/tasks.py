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
from users.models import ResourceUser, ToDoUser, UserCondition


def process_condition(condition_id, user_id, send_email=True):
    """
    Processing triggered condition

    :param condition_id int: the condition that got triggered
    :param user_id int: the user that it got triggered for
    :param send_email bool: should send update email (not for portal)
    """

    condition = Condition.objects.get(id=condition_id)
    user = get_user_model().objects.get(id=user_id)
    condition.process_condition(user)

    # Send notifications to user
    notifications = Notification.objects.filter(
        notification_type__in=[
            Notification.Type.ADDED_TODO,
            Notification.Type.ADDED_RESOURCE,
            Notification.Type.ADDED_BADGE,
            Notification.Type.ADDED_INTRODUCTION,
        ],
        created_for=user,
        notified_user=False,
    )

    if not notifications.exists():
        return

    if user.has_slack_account:
        to_do_blocks = [
            SlackToDo(
                ToDoUser.objects.get(to_do__id=notif.item_id, user=user), user
            ).get_block()
            for notif in notifications.filter(
                notification_type=Notification.Type.ADDED_TODO
            )
        ]

        resource_blocks = [
            SlackResource(
                ResourceUser.objects.get(user=user, resource__id=notif.item_id), user
            ).get_block()
            for notif in notifications.filter(
                notification_type=Notification.Type.ADDED_RESOURCE
            )
        ]

        badge_blocks = []
        for notif in notifications.filter(
            notification_type=Notification.Type.ADDED_BADGE
        ):
            badge_blocks.append(
                paragraph(
                    _("*Congrats, you unlocked: %(item_name)s *")
                    % {
                        "item_name": user.personalize(
                            Badge.objects.get(id=notif.item_id).name
                        ),
                    },
                ),
            )
            badge_blocks += Badge.objects.get(id=notif.item_id).to_slack_block(user)

        intro_blocks = [
            SlackIntro(Introduction.objects.get(id=notif.item_id), user).format_block()
            for notif in notifications.filter(
                notification_type=Notification.Type.ADDED_INTRODUCTION
            )
        ]

        if len(to_do_blocks):
            # Send to do items separate as we need to update this block
            Slack().send_message(
                text=_("Here are some new items for you!"),
                blocks=[
                    paragraph(_("Here are some new items for you!")),
                    *to_do_blocks,
                ],
                channel=user.slack_user_id,
            )

            if len(resource_blocks) or len(badge_blocks) or len(intro_blocks):
                Slack().send_message(
                    text=_("Here are some new items for you!"),
                    blocks=[
                        *intro_blocks,
                        *badge_blocks,
                        *resource_blocks,
                    ],
                    channel=user.slack_user_id,
                )

        else:
            Slack().send_message(
                text=_("Here are some new items for you!"),
                blocks=[
                    paragraph(_("Here are some new items for you!")),
                    *intro_blocks,
                    *badge_blocks,
                    *resource_blocks,
                ],
                channel=user.slack_user_id,
            )
    elif send_email:
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
    if org is None:
        return

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

        # all users excluding those who are offboarding
        for user in get_user_model().objects.exclude(termination_date__isnull=False):
            current_time = user.get_local_time(last_updated).time()

            before_conditions = UserCondition.objects.filter(
                user=user,
                condition__condition_type=Condition.Type.BEFORE
            ).distinct("base_date")
            after_conditions = UserCondition.objects.filter(
                user=user,
                condition__condition_type=Condition.Type.AFTER
            ).distinct("base_date")
            before_date_day_map = {
                con.base_date: user.days_before_starting(con.base_date) for con in before_conditions
            }
            after_date_day_map = {
                con.base_date: user.workday(con.base_date)
                for con in after_conditions
            }

            # Get conditions before/after they started
            conditions = Condition.objects.none()
            # Before starting
            for base_date, days_before_starting in before_date_day_map.items():
                conditions |= UserCondition.objects.filter(
                    user=user,
                    base_date=base_date,
                    condition__condition_type=Condition.Type.BEFORE,
                    condition__days=days_before_starting,
                    condition__time=current_time,
                )
            if user.get_local_time(last_updated).weekday() < 5:
                # On workday x
                for base_date, workday in after_date_day_map.items():
                    conditions |= UserCondition.objects.filter(
                        user=user,
                        base_date=base_date,
                        condition__condition_type=Condition.Type.AFTER,
                        condition__days=workday,
                        condition__time=current_time,
                    )

            # Schedule conditions to be executed with new scheduled task, we do this to
            # avoid long standing tasks. I.e. sending lots of emails might take more
            # time.
            for i in conditions:
                async_task(
                    process_condition,
                    i.condition.id,
                    user.id,
                    task_name=f"Process condition: {i.condition.id} for {user.full_name}",
                )

        for user in get_user_model().offboarding.all():
            amount_days_before = user.days_before_termination_date

            if (
                amount_days_before == -1
                or user.get_local_time(last_updated).weekday() > 4  # 5 or 6 is weekend
            ):
                # we are past the termination date or in a weekend, move to the next
                continue

            current_time = user.get_local_time(last_updated).time()
            conditions = user.conditions.filter(
                condition_type=Condition.Type.BEFORE,
                days=amount_days_before,
                time=current_time,
            )

            # Schedule conditions to be executed with new scheduled task, we do this to
            # avoid long standing tasks. I.e. sending lots of emails might take more
            # time.
            for i in conditions:
                async_task(
                    process_condition,
                    i.id,
                    user.id,
                    task_name=f"Process condition: {i.id} for {user.full_name}",
                )
