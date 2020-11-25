from django.contrib.auth import get_user_model
import slack
from django.utils.translation import ugettext as _
from django.utils import translation
from django.conf import settings
from integrations.models import AccessToken
from organization.models import Organization
from django.template import Context, Template
from introductions.models import Introduction

from resources.models import Chapter


class Slack:
    def __init__(self, response=None):
        team = AccessToken.objects.get(integration=0)

        self.team = team
        self.client = slack.WebClient(token=self.team.bot_token)
        self.org = Organization.object.get()
        self.user_obj = None
        self.channel = None

        if response is not None:
            if 'event' in response:
                self.event = response['event']
                if 'message' in self.event:
                    self.user = self.event['message']['user']
                if 'user' in self.event:
                    self.user = self.event['user']
                if 'text' in self.event:
                    self.text = self.event['text'].lower().strip()
            if 'container' in response:
                self.container = response['container']

            if 'user' in response:
                self.user = response['user']['id']
            if get_user_model().objects.filter(slack_user_id=self.user).exists():
                user = get_user_model().objects.get(slack_user_id=self.user)
                self.user_obj = user
                self.channel = user.slack_channel_id
                translation.activate(self.user_obj.language)

    def get_channels(self):
        try:
            response = self.client.api_call(
                "conversations.list",
                data={
                    'exclude_archived': True,
                    'types': 'public_channel,private_channel'
                }
            )
        except Exception:
            return []
        return [x['name'] for x in response['channels']]

    def get_all_users(self):
        try:
            response = self.client.api_call("users.list")
        except Exception:
            return []
        return response['members']

    def find_by_email(self, email):
        try:
            response = self.client.api_call("users.lookupByEmail", data={'email': email})
        except Exception:
            return False
        return response

    def personalize(self, message):
        if self.user_obj is not None:
            c = Context({
                'first_name': self.user_obj.first_name,
                'last_name': self.user_obj.last_name,
                'email': self.user_obj.email,
                'position': self.user_obj.position,
                'start': self.user_obj.start_day,
                'manager': self.user_obj.manager.full_name() if self.user_obj.manager is not None else '',
                'buddy': self.user_obj.buddy.full_name() if self.user_obj.buddy is not None else '',
            })
        else:
            c = Context({'first_name': '', 'last_name': '',
                         'email': '', 'position': '', 'start': '',
                         'manager': '', 'buddy': ''})
        message = message.replace('<p>', '')
        message = message.replace('</p>', '')
        t = Template(message)
        return t.render(c)

    def send_message(self, attachments=None, blocks=None, channel=None, text=None):
        # if user is unknown in system, don't send message
        if channel is None and self.channel is None and self.user is None:
            return False

        if blocks is None:
            blocks = []
        if channel is None:
            if self.channel is None:
                channel = self.user
            else:
                channel = self.channel
        if text is not None:
            blocks = self.format_simple_text(text)
        return self.client.chat_postMessage(channel=channel, blocks=blocks, as_user=True,
                                            username=self.team.bot_id)

    def update_message(self, ts, blocks=None):
        if blocks is None:
            blocks = []
        channel = self.channel
        return self.client.chat_update(channel=channel, ts=ts, blocks=blocks, as_user=True,
                                       username=self.team.bot_id)

    def update_to_do_message(self, ts, block_ids, remove_item):
        # hacky, but otherwise we get a circular import
        from users.models import ToDoUser

        to_do_ids = eval(block_ids)
        text = to_do_ids.pop(0)
        to_do_ids = list(map(int, to_do_ids))
        index_item = to_do_ids.index(remove_item)
        to_do_ids.pop(index_item)

        items = ToDoUser.objects.filter(pk__in=to_do_ids)
        if items.count() == 0:
            text = 'You did all the things I mentioned in this message!'
        blocks = self.format_to_do_block(pre_message=text, items=items)
        self.update_message(ts, blocks)

    def set_user(self, user):
        self.user_obj = user
        self.user = user.slack_user_id
        self.channel = user.slack_channel_id
        translation.activate(user.language)

    def format_simple_text(self, text):
        return [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }]

    def has_account(self):
        return get_user_model().objects.filter(slack_user_id=self.user).exists()

    def footer_text(self, item):
        workday = self.user_obj.workday()
        if item.due_on_day == 0:
            return _("This task has no deadline.")
        if (item.due_on_day - workday) < 0:
            return _("This task is overdue")
        if (item.due_on_day - workday) == 0:
            return _("This task is due today")
        return _("This task needs to be completed in ") + str(item.due_on_day - workday) + _(" working days.")

    def format_to_do_block(self, pre_message, items):
        blocks = [{
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": pre_message
            }
        }]
        for i in items:
            if i.to_do.valid_for_slack():
                text = '*' + self.personalize(i.to_do.name) + '*\n' + self.footer_text(i.to_do)
                value = "dialog:to_do:" + str(i.id)
                action_text = "View details"
            else:
                action_text = "Mark completed"
                value = "to_do:external:" + str(i.id)
                text = "*" + i.to_do.name + "* <" + settings.BASE_URL + "/#/slackform?token=" + self.user_obj.unique_url + "&id=" + str(
                    i.id) + "|View details>\n" + self.footer_text(i.to_do)
            blocks.append({
                "type": "section",
                "block_id": str(i.id),
                "text": {
                    "type": "mrkdwn",
                    "text": text
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": action_text
                    },
                    "value": value
                }
            })
        return blocks

    def format_resource_block(self, items, pre_message):
        blocks = []
        if pre_message is not None:
            blocks = [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": pre_message
                }
            }]

        for i in items:
            if i.resource.course and not i.completed_course:
                value = "dialog:course:" + str(i.id) + ':' + str(i.resource.chapters.filter(type=0).first().id)
                action_text = "View course"
            else:
                action_text = "View resource"
                value = "dialog:resource:" + str(i.id) + ':' + str(i.resource.chapters.filter(type=0).first().id)
            blocks.append({
                "type": "section",
                "block_id": str(i.id),
                "text": {
                    "type": "mrkdwn",
                    "text": "*" + self.personalize(i.resource.name) + "*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": action_text
                    },
                    "value": value
                }
            })
        return blocks

    def format_into_block(self, intro):
        text = '*' + intro.name + ':* ' + intro.intro_person.full_name() + '\n'
        if intro.intro_person.position is not None and intro.intro_person.position != '':
            text += intro.intro_person.position + '\n'
        if intro.intro_person.message is not None and intro.intro_person.message != "":
            text += '_' + s.personalize(intro.intro_person.message) + '_\n'
        if intro.intro_person.email is not None and intro.intro_person.email != "":
            text += intro.intro_person.email + ' '
        if intro.intro_person.phone is not None and intro.intro_person.phone != "":
            text += intro.intro_person.phone
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
        if intro.intro_person.profile_image is not None:
            block["accessory"] = {
                "type": "image",
                "image_url": intro.intro_person.profile_image.get_url(),
                "alt_text": "profile image"
            }
        return block

    def open_modal(self, trigger_id, title, blocks, callback, private_metadata, submit_name):
        if submit_name is None:
            submit_name = 'Done'
        view = {
            "type": "modal",
            "callback_id": callback,
            "title": {
                "type": "plain_text",
                "text": title if len(title) < 24 else title[:20] + '...'
            },
            "submit": {
                "type": "plain_text",
                "text": submit_name
            },
            "blocks": blocks,
            "private_metadata": private_metadata
        }
        self.client.views_open(trigger_id=trigger_id, view=view)

    def send_sequence_triggers(self, items, to_do_user):
        from users.models import ToDoUser
        if len(items['introductions']):
            for i in items['introductions']:
                blocks.append(s.format_intro_block(Introduction.objects.get(id=i.id)))
            self.send_message(blocks=blocks)
        for i in items['badges']:
            blocks = [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Congrats, you unlocked: " + self.personalize(i.name) + "*"
                }
            }]
            for j in i.content.all():
                blocks.append(j.to_slack_block(self.user_obj))
            self.send_message(blocks=blocks)
        if len(items['to_do']):
            to_do = [ToDoUser.objects.get(user=self.user_obj, to_do=i) for i in items['to_do']]
            if len(items['to_do']) > 1:
                pre_message = "We have just added these new to do items:"
            else:
                pre_message = "We have just added a new to do item for you:"
            blocks = self.format_to_do_block(pre_message=pre_message, items=to_do)
            self.send_message(blocks=blocks)
        # send response from to do item back to channel
        if to_do_user is not None and to_do_user.to_do.send_back:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Our new hire " + to_do_user.user.first_name + " just answered some questions:*"
                    }
                },
                {"type": "divider"}
            ]
            for i in to_do_user.form:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*" + i["text"] + "*\n" + i["value"]
                    }
                })
            self.send_message(blocks=blocks, channel=to_do_user.to_do.channel)

    def create_buttons(self, categories):
        blocks = []
        if len(categories) == 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "No resources available"
                }
            })
        for i in categories:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": i['name']
                        },
                        "value": "category:" + str(i['id']),
                        "action_id": "category:" + str(i['id'])
                    }
                ]
            })
        return blocks

    def create_updated_view(self, value, view, course_completed):
        chapter = Chapter.objects.get(id=value)
        blocks = []
        if course_completed or (view['blocks'][0]['type'] == 'select_static' and not chapter.type == 2):
            blocks = [view['blocks'][0]]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*" + chapter.name + "*"
            }
        })
        for i in chapter.content.all():
            blocks.append(i.to_slack_block(self.user_obj))
        view['blocks'] = blocks
        del view['team_id']
        del view['state']
        del view['hash']
        del view['previous_view_id']
        del view['root_view_id']
        del view['app_id']
        del view['app_installed_team_id']
        del view['bot_id']
        del view['id']
        view['callback_id'] = view['callback_id'].rsplit(':', 1)[0] + ':' + str(chapter.id)
        view['close'] = {'type': 'plain_text', 'text': 'Close', 'emoji': True}
        return view

    def help(self):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _("Happy to help! Here are all the things you can say to me: \n\n")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '*' + _("What do I need to do today?") + '*\n' + _(
                        "This will show all the tasks you need to do today. I will show you these every day as well, but just incase you want to get them again.")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '*' + _("Do I have any to do items that are overdue?") + '*\n' + _(
                        "This will show all tasks that should have been completed. Please do those as soon as possible.")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '*' + _("Show me all to do items") + '*\n' + _("This will show all tasks")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '*' + _("Show me all resources") + '*\n' + _("This will show all resources.")
                }
            }]
        self.send_message(blocks=blocks)
