from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.formats import localize
from django.utils.translation import gettext as _

from admin.integrations.models import Integration
from organization.models import Organization, WelcomeMessage
from slack_bot.slack_intro import SlackIntro
from slack_bot.slack_misc import get_new_hire_first_message_buttons
from slack_bot.slack_resource import SlackResource
from slack_bot.slack_to_do import SlackToDoManager
from slack_bot.utils import Slack, actions, button, paragraph
from users.models import ResourceUser, ToDoUser


def link_slack_users(users=[]):
    # Drop if Slack is not enabled
    if (
        not Integration.objects.filter(integration=0).exists()
        and settings.SLACK_APP_TOKEN == ""
    ):
        return

    slack = Slack()
    org = Organization.object.get()

    if len(users) == 0:
        users = get_user_model().new_hires.without_slack()

    for user in users:
        response = slack.find_by_email(email=user.email.lower())
        if response:
            translation.activate(user.language)
            user.slack_user_id = response["user"]["id"]
            user.save()

            # Personalized message for user (slack welcome message)
            blocks = [
                paragraph(
                    user.personalize(
                        WelcomeMessage.objects.get(
                            language=user.language, message_type=3
                        ).message
                    ),
                )
            ]

            # Check if extra buttons need to be send with it as well
            if org.slack_buttons:
                blocks.extend(get_new_hire_first_message_buttons())

            # Adding introduction items
            blocks.extend(
                [
                    SlackIntro(intro, user).format_block()
                    for intro in user.introductions.all()
                ]
            )

            res = Slack().send_message(
                blocks=blocks, text=_("Welcome!"), channel=user.slack_user_id
            )
            user.slack_channel_id = res["channel"]
            user.save()

            # Send user to do items for that day (and perhaps overdue ones)
            tasks = ToDoUser.objects.overdue(user) | ToDoUser.objects.due_today(user)

            if tasks.exists():
                blocks = SlackToDoManager(user).get_blocks(
                    tasks.values_list("id", flat=True),
                    text=_("These are the tasks you need to complete:"),
                )
                Slack().send_message(
                    blocks=blocks,
                    text=_("These are the tasks you need to complete:"),
                    channel=user.slack_user_id,
                )


def update_new_hire():
    if (
        not Integration.objects.filter(integration=0).exists()
        and settings.SLACK_APP_TOKEN == ""
    ):
        return

    for user in get_user_model().new_hires.with_slack():
        local_datetime = user.get_local_time()

        if not (
            local_datetime.hour == 8
            and local_datetime.weekday() < 5
            and local_datetime.date() >= user.start_day
        ):
            continue

        translation.activate(user.language)

        overdue_items = ToDoUser.objects.overdue(user)
        tasks = ToDoUser.objects.due_today(user) | overdue_items

        courses_due = ResourceUser.objects.filter(resource__on_day__lte=user.workday)
        # Filter out completed courses
        course_blocks = [
            SlackResource(course, user).get_block()
            for course in courses_due
            if course.is_course
        ]

        # If any overdue tasks exist, then notify the user
        if tasks.exists():
            if overdue_items.exists():
                text = _(
                    "Good morning! These are the tasks you need to complete. Some to "
                    "do items are overdue. Please complete those as soon as possible!"
                )
            else:
                text = _(
                    "Good morning! These are the tasks you need to complete today:"
                )

            blocks = SlackToDoManager(user).get_blocks(
                tasks.values_list("id", flat=True),
                text=text,
            )
            Slack().send_message(
                blocks=course_blocks,
                text=_("Here are some courses that you need to complete"),
                channel=user.slack_user_id,
            )
            Slack().send_message(blocks=blocks, text=text, channel=user.slack_user_id)


def first_day_reminder():
    org = Organization.object.get()
    # If Slack doesn't exist or setting is disabled, then drop
    if (
        not Integration.objects.filter(integration=0).exists()
        or not org.send_new_hire_start_reminder
    ):
        return

    # Getting new hires starting today. Base on org default language.
    translation.activate(org.language)
    local_time_date = org.current_datetime
    starting_today = get_user_model().new_hires.starting_today()

    # Check if it's 8 am (org time) and if there are any
    if local_time_date.hour == 8 and starting_today.exists():
        if starting_today.count() == 1:
            text = _("Just a quick reminder: It's %(name)s's first day today!") % {
                "name": starting_today.first().full_name
            }
        else:
            names = ", ".join([new_hire.full_name for new_hire in starting_today])
            text = _(
                "We got some new hires coming in! %(names)s are starting today!"
            ) % {"names": names}
        send_to = (
            org.slack_default_channel.name
            if org.slack_default_channel is not None
            else "general"
        )
        Slack().send_message(text=text, channel="#" + send_to)


def introduce_new_people():
    org = Organization.object.get()
    # If Slack doesn't exist or setting is disabled, then drop
    if (
        not Integration.objects.filter(integration=0).exists()
        or not org.ask_colleague_welcome_message
    ):
        return

    new_hires = get_user_model().new_hires.to_introduce()

    # If there are no new hires starting, then drop
    if not new_hires.exists():
        return

    translation.activate(org.language)

    blocks = []
    if new_hires.count() > 1:
        text = _(
            "We got some new hires coming in soon! Make sure to leave a welcome "
            "message for them!"
        )
    else:
        text = _(
            "We have a new hire coming in soon! Make sure to leave a message for "
            "%(first_name)s!"
        ) % {"first_name": new_hires.first().first_name}

    blocks.append(paragraph(text))

    for new_hire in new_hires:
        message = f"*{new_hire.full_name}*"

        # Add new hire introduction message
        if new_hire.message != "":
            message += f"\n_{new_hire.personalize(new_hire.message)}_"

        block = paragraph(message)

        # Add profile image
        if new_hire.profile_image:
            block["accessory"] = {
                "type": "image",
                "image_url": new_hire.profile_image.get_url(),
                "alt_text": "profile image",
            }

        blocks.append(block)

        # If position is filled, then add that
        footer_extra = ""
        if new_hire.position != "":
            footer_extra = _(" and is our new %(position)s") % {
                "position": new_hire.position
            }

        # Add when the new hire starts
        start_text = _("%(first_name)s starts on %(start_day)s%(footer_extra)s.") % {
            "first_name": new_hire.first_name,
            "start_day": localize(new_hire.start_day),
            "footer_extra": footer_extra,
        }

        blocks.append(paragraph(start_text))

        # Add block to send personal message
        blocks.append(
            actions(
                [
                    button(
                        text=_("Welcome this new hire!"),
                        action_id="dialog:welcome",
                        style="primary",
                        value=str(new_hire.id),
                    )
                ]
            )
        )

    send_to = (
        org.slack_default_channel.name
        if org.slack_default_channel is not None
        else "general"
    )
    Slack().send_message(channel="#" + send_to, text=text, blocks=blocks)

    # Make sure they aren't introduced again
    new_hires.update(is_introduced_to_colleagues=True)
