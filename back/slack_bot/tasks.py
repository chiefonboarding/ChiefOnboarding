from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.formats import localize
from django.utils.translation import ugettext as _

from admin.integrations.models import AccessToken
from organization.models import Organization, WelcomeMessage
from slack_bot.slack import Slack
from users.models import ToDoUser


def link_slack_users(users=[]):
    if not AccessToken.objects.filter(integration=0).exists():
        return
    s = Slack()

    if len(users) == 0:
        users = get_user_model().new_hires.filter(slack_user_id="")

    for user in users:
        response = s.find_by_email(email=user.email.lower())
        if response:
            translation.activate(user.language)
            user.slack_user_id = response["user"]["id"]
            user.save()
            s.set_user(user)
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": s.personalize(
                            WelcomeMessage.objects.get(
                                language=user.language, message_type=3
                            ).message
                        ),
                    },
                }
            ]
            # check if extra buttons need to be send with it as well
            if s.org.slack_buttons:
                blocks.extend(
                    [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": _("Click a button to see more information :)"),
                            },
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": _("To do items"),
                                    },
                                    "value": "to_do",
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": _("Resources")},
                                    "value": "resources",
                                },
                            ],
                        },
                    ]
                )

            # adding introduction items
            introductions = user.introductions.all()
            for i in introductions:
                blocks.append(s.format_intro_block(i))

            res = s.send_message(blocks=blocks, channel=response["user"]["id"])
            user.slack_channel_id = res["channel"]
            user.save()
            # send user to do items for that day (and perhaps over due ones)
            tasks = ToDoUser.objects.filter(
                user=user, completed=False, to_do__due_on_day__lte=user.workday()
            ).exclude(to_do__due_on_day=0)

            if tasks.exists():
                blocks = s.format_to_do_block(
                    pre_message=_("These are the tasks you need to complete:"),
                    items=tasks,
                )
                s.send_message(blocks=blocks)

    return True


def update_new_hire():
    if not AccessToken.objects.filter(integration=0).exists():
        return
    s = Slack()

    for user in get_user_model().new_hires.exclude(slack_user_id=""):
        local_datetime = user.get_local_time()
        if (
            local_datetime.hour == 8
            and local_datetime.weekday() < 5
            and local_datetime.date() >= user.start_day
        ):
            s.set_user(user)
            translation.activate(user.language)

            # overdue items
            tasks = ToDoUser.objects.filter(
                user=user, completed=False, to_do__due_on_day__lt=user.workday()
            ).exclude(to_do__due_on_day=0)
            if tasks.exists():
                # If any overdue tasks exist, then notify the user
                blocks = s.format_to_do_block(
                    pre_message=_(
                        "Some to do items are overdue. Please complete those as "
                        "soon as possible!"
                    ),
                    items=tasks,
                )
                s.send_message(blocks=blocks)

            # to do items for today
            tasks = ToDoUser.objects.filter(
                user=user, completed=False, to_do__due_on_day=user.workday()
            )

            if tasks.exists():
                # If any tasks exist that are due today, then notify the user
                blocks = s.format_to_do_block(
                    pre_message=_(
                        "Good morning! These are the tasks you need to complete today:"
                    ),
                    items=tasks,
                )
                s.send_message(blocks=blocks)
    return


def first_day_reminder():
    org = Organization.object.get()
    if (
        not AccessToken.objects.filter(integration=0).exists()
        or not org.send_new_hire_start_reminder
    ):
        return
    translation.activate(org.language)
    user = get_user_model().admins.first()
    local_time_date = user.get_local_time()
    new_hires_starting_today = get_user_model().new_hires.filter(
        start_day=datetime.now().date()
    )
    if (
        local_time_date.hour == 8
        and org.send_new_hire_start_reminder
        and new_hires_starting_today.exists()
    ):
        text = ""
        if new_hires_starting_today.count() == 1:
            text = (
                _("Just a quick reminder: It's %(name)'s first day today!") % {'name': user.full_name}
            )
        else:
            for i in new_hires_starting_today:
                text += i.get_full_name() + ", "
            # remove last comma
            text = text[:-2]
            text = (
                _("We got some new hires coming in! %(names) are starting today!") % {'names': text}
            )
        s = Slack()
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
        s.send_message(blocks=blocks, channel="#" + org.slack_default_channel)

    return True


def introduce_new_people():
    org = Organization.object.get()
    if (
        not AccessToken.objects.filter(integration=0).exists()
        or not org.ask_colleague_welcome_message
    ):
        return
    s = Slack()
    translation.activate(org.language)
    new_hires = get_user_model().new_hires.filter(
        is_introduced_to_colleagues=False, start_day__gt=datetime.now().date()
    )
    if new_hires.exists():
        blocks = []
        if new_hires.count() > 1:
            text = _(
                "We got some new hires coming in soon! Make sure to leave a welcome message for them!"
            )
        else:
            text = _("We have a new hire coming in soon! Make sure to leave a message for %(first_name)s!") % {'first_name': new_hires.first().first_name }
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

        for new_hire in new_hires:
            message = f"*{new_hire.full_name}*"
            if new_hire.message != "":
                message += f"\n_{new_hire.message}_"
            block = {"type": "section", "text": {"type": "mrkdwn", "text": message}}
            if new_hire.profile_image:
                block["accessory"] = {
                    "type": "image",
                    "image_url": new_hire.profile_image.get_url(),
                    "alt_text": "profile image",
                }
            blocks.append(block)
            footer_extra = ""
            if new_hire.position != "":
                footer_extra = _(" and is our new %(postition)s") % {'position': new_hire.position}
            context = _("%(first_name)s starts on %(start_day)s %(footer_extra)s.") % {'first_name': new_hire.first_name, 'start_day': localize(new_hire.start_day), 'footer_extra': footer_extra}
            blocks.append(
                {
                    "type": "context",
                    "elements": [{"type": "plain_text", "text": context}],
                }
            )
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": _("Welcome this new hire!"),
                            },
                            "value": "dialog:welcome:" + str(new_hire.id),
                        }
                    ],
                }
            )
            new_hire.is_introduced_to_colleagues = True
            new_hire.save()
        s.send_message(channel="#" + org.slack_default_channel, blocks=blocks)
