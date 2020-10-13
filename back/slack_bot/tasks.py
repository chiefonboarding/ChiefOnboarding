from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.formats import localize

from organization.models import WelcomeMessage
from slack_bot.slack import Slack
from django.utils.translation import ugettext as _

from users.models import ToDoUser
from organization.models import Organization
from datetime import datetime

from integrations.models import AccessToken


@periodic_task(run_every=(crontab(minute='*/15')), name="link_slack_users", ignore_result=True)
def link_slack_users():
    if not AccessToken.objects.filter(integration=0).exists():
        return
    s = Slack()

    for user in get_user_model().objects.filter(slack_user_id__isnull=True, role=0):
        response = s.find_by_email(email=user.email.lower())
        if response:
            translation.activate(user.language)
            user.slack_user_id = response['user']['id']
            user.save()
            s.set_user(user)
            blocks = [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": WelcomeMessage.objects.get(language=user.language, message_type=3).message
                },
            }]
            # check if extra buttons need to be send with it as well
            if s.org.slack_buttons:
                blocks.extend(
                    [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": _("Click a button to see more information :)")
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "To do items"
                                    },
                                    "value": "to_do"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Resources"
                                    },
                                    "value": "resources"
                                }
                            ]
                        }
                    ])

            # adding introduction items
            introductions = user.introductions.all()
            if introductions.exists():
                for i in introductions:
                    text = '*' + i.name + ':* ' + i.intro_person.full_name() + '\n'
                    if i.intro_person.position is not None and i.intro_person.position != '':
                        text += i.intro_person.position + '\n'
                    if i.intro_person.message is not None and i.intro_person.message != "":
                        text += '_' + s.personalize(i.intro_person.message) + '_\n'
                    if i.intro_person.email is not None and i.intro_person.email != "":
                        text += i.intro_person.email + ' '
                    if i.intro_person.phone is not None and i.intro_person.phone != "":
                        text += i.intro_person.phone
                    block = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    }
                    if i.intro_person.profile_image is not None:
                        block["accessory"] = {
                            "type": "image",
                            "image_url": i.intro_person.profile_image.get_url(),
                            "alt_text": "profile image"
                        }

                    blocks.append(block)
            res = s.send_message(
                blocks=blocks,
                channel=response['user']['id']
            )
            user.slack_channel_id = res['channel']
            user.save()
            # send user to do items for that day (and perhaps over due ones)
            tasks = ToDoUser.objects.filter(
                user=user,
                completed=False,
                to_do__due_on_day__lte=user.workday()
            ).exclude(to_do__due_on_day=0)

            if tasks.exists():
                blocks = s.format_to_do_block(pre_message=_("These are the tasks you need to complete:"), items=tasks)
                s.send_message(blocks=blocks)

    return True


@periodic_task(run_every=(crontab(minute='10')), name="update_new_hire", ignore_result=True)
def update_new_hire():
    if not AccessToken.objects.filter(integration=0).exists():
        return
    s = Slack()

    for user in get_user_model().objects.filter(slack_user_id__isnull=False, role=0):
        local_datetime = user.get_local_time()
        if local_datetime.hour == 8 and local_datetime.weekday() < 5 and local_datetime.date() >= user.start_day:
            s.set_user(user)
            # overdue items
            tasks = ToDoUser.objects.filter(
                user=user,
                completed=False,
                to_do__due_on_day__lt=user.workday()
            ).exclude(to_do__due_on_day=0)
            if tasks.exists():
                blocks = s.format_to_do_block(pre_message=_("Some to do items are overdue. Please complete those as "
                                                            "soon as possible!"), items=tasks)
                s.send_message(blocks=blocks)

            # to do items for today
            tasks = ToDoUser.objects.filter(
                user=user,
                completed=False,
                to_do__due_on_day=user.workday()
            )
            if tasks.exists():
                blocks = s.format_to_do_block(pre_message=_("Good morning! These are the tasks you need to complete "
                                                            "today:"), items=tasks)
                s.send_message(blocks=blocks)
    return


@periodic_task(run_every=(crontab(minute='0')), name="first_day_reminder", ignore_result=True)
def first_day_reminder():
    org = Organization.object.get()
    if not AccessToken.objects.filter(integration=0).exists() or not org.send_new_hire_start_reminder:
        return
    translation.activate(org.language)
    user = get_user_model().objects.filter(role=1).first()
    us_state = user.get_local_time()
    new_hires_starting_today = get_user_model().objects.filter(start_day=datetime.now().date(), role=0)
    if us_state.hour == 8 and org.send_new_hire_start_reminder and new_hires_starting_today.exists():
        text = ''
        if new_hires_starting_today.count() == 1:
            text = _("Just a quick reminder: It's ") + user.full_name + _("'s first day today!")
        else:
            for i in new_hires_starting_today:
                text += i.get_full_name() + ', '
            # remove last comma
            text = text[:-2]
            text = _("We got some new hires coming in! ") + text + _(" are starting today!")
        s = Slack()
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }]
        s.send_message(blocks=blocks, channel="#general")

    return True


@periodic_task(run_every=(crontab(minute=0)), name="introduce_new_people", ignore_result=True)
def introduce_new_people():
    org = Organization.object.get()
    if not AccessToken.objects.filter(integration=0).exists() or not org.ask_colleague_welcome_message:
        return
    s = Slack()
    translation.activate(org.language)
    new_hires = get_user_model().objects.filter(
        is_introduced_to_colleagues=False,
        role=0,
        start_day__gt=datetime.now().date()
    )
    if new_hires.exists():
        blocks = []
        if new_hires.count() > 1:
            text = _("We got some new hires coming in soon! Make sure to leave a welcome message for them!")
        else:
            text = _(
                "We have a new hire coming in soon! Make sure to leave a message for ") + new_hires.first().first_name + "!"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })

        for new_hire in new_hires:
            message = "*" + new_hire.full_name() + "*"
            if new_hire.message != "":
                message += "\n_" + new_hire.message + "_"
            block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
            if new_hire.profile_image:
                block["accessory"] = {
                    "type": "image",
                    "image_url": new_hire.profile_image.get_url(),
                    "alt_text": "profile image"
                }
            blocks.append(block)
            footer_extra = ""
            if new_hire.position is not None and new_hire.position != "":
                footer_extra = _(" and is our new ") + new_hire.position
            context = new_hire.first_name + _(" starts on ") + localize(new_hire.start_day) + footer_extra + "."
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "plain_text",
                    "text": context
                }]
            })
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": _("Welcome this new hire!")
                        },
                        "value": "dialog:welcome:" + str(new_hire.id)
                    }
                ]
            })
            new_hire.is_introduced_to_colleagues = True
            new_hire.save()
        s.send_message(channel="#general", blocks=blocks)
