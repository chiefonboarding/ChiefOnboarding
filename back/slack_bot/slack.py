import slack_sdk as slack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.utils import translation
from django.utils.translation import ugettext as _

from admin.integrations.models import AccessToken
from admin.introductions.models import Introduction
from admin.resources.models import Chapter
from organization.models import Organization


class Slack:
    def __init__(self, response=None):
        team = AccessToken.objects.get(integration=0)

        self.team = team
        self.client = slack.WebClient(token=self.team.bot_token)
        self.org = Organization.object.get()
        self.user_obj = None
        self.channel = None

        if response is not None:
            if "event" in response:
                self.event = response["event"]
                if "message" in self.event:
                    self.user = self.event["message"]["user"]
                if "user" in self.event:
                    self.user = self.event["user"]
                if "text" in self.event:
                    self.text = self.event["text"].lower().strip()
            if "container" in response:
                self.container = response["container"]

            if "user" in response:
                self.user = response["user"]["id"]
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
                    "exclude_archived": True,
                    "types": "public_channel,private_channel",
                },
            )
        except Exception as e:
            return []
        return [[x["name"], x["is_private"]] for x in response["channels"]]

    def get_all_users(self):
        try:
            response = self.client.api_call("users.list")
        except Exception:
            return []
        return response["members"]

    def find_by_email(self, email):
        try:
            response = self.client.api_call(
                "users.lookupByEmail", data={"email": email}
            )
        except Exception:
            return False
        return response

    def find_user_by_id(self, id):
        try:
            response = self.client.api_call("users.info", data={"user": id})["user"]
        except Exception:
            return False
        return response

    def personalize(self, message):
        if self.user_obj is not None:
            c = Context(
                {
                    "first_name": self.user_obj.first_name,
                    "last_name": self.user_obj.last_name,
                    "email": self.user_obj.email,
                    "position": self.user_obj.position,
                    "start": self.user_obj.start_day,
                    "manager": self.user_obj.manager.full_name()
                    if self.user_obj.manager is not None
                    else "",
                    "buddy": self.user_obj.buddy.full_name()
                    if self.user_obj.buddy is not None
                    else "",
                }
            )
        else:
            c = Context(
                {
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "position": "",
                    "start": "",
                    "manager": "",
                    "buddy": "",
                }
            )
        message = message.replace("<p>", "")
        message = message.replace("</p>", "")
        t = Template(message)
        return t.render(c)

    def send_message(self, blocks=[], channel="", text=""):
        # if user is unknown in system, don't send message
        if (channel == "" and self.channel == "") or self.user is None:
            return False

        if channel is "":
            if self.channel is "":
                channel = self.user
            else:
                channel = self.channel
        if text != "":
            blocks = self.format_simple_text(text)
        return self.client.chat_postMessage(
            channel=channel, blocks=blocks, as_user=True, username=self.team.bot_id
        )

    def update_message(self, ts, blocks=None):
        if blocks is None:
            blocks = []
        channel = self.channel
        return self.client.chat_update(
            channel=channel,
            ts=ts,
            blocks=blocks,
            as_user=True,
            username=self.team.bot_id,
        )

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
            text = _("You did all the things I mentioned in this message!")
        blocks = self.format_to_do_block(pre_message=text, items=items)
        self.update_message(ts, blocks)

    def set_user(self, user):
        self.user_obj = user
        self.user = user.slack_user_id
        self.channel = user.slack_channel_id
        translation.activate(user.language)

    def format_simple_text(self, text):
        return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]

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
        return _("This task needs to be completed in %(amount)s working days") % {
            "amount": str(item.due_on_day - workday)
        }

    def format_to_do_block(self, pre_message, items):
        blocks = [
            {"type": "section", "text": {"type": "plain_text", "text": pre_message}}
        ]
        for i in items:
            if i.to_do.valid_for_slack():
                text = (
                    f"*{self.personalize(i.to_do.name)}*\n{self.footer_text(i.to_do)}"
                )
                value = "dialog:to_do:" + str(i.id)
                action_text = "View details"
            else:
                action_text = "Mark completed"
                value = "to_do:external:" + str(i.id)
                text = (
                    f"*{i.to_do.name}* <{settings.BASE_URL}/#/slackform?token={self.user_obj.unique_url}&id={str(i.id)}|"
                    + _("View details")
                    + f">\n{self.footer_text(i.to_do)}"
                )
            blocks.append(
                {
                    "type": "section",
                    "block_id": str(i.id),
                    "text": {"type": "mrkdwn", "text": text},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": action_text},
                        "value": value,
                    },
                }
            )
        return blocks

    def format_resource_block(self, items, pre_message):
        blocks = []
        if pre_message is not None:
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": pre_message}}
            ]

        for i in items:
            if i.resource.course and not i.completed_course:
                value = "dialog:course:{i.id}:{i.resource.chapters.filter(type=0).first().id}"
                action_text = _("View course")
            else:
                action_text = _("View resource")
                value = "dialog:resource:{i.id}:{i.resource.chapters.filter(type=0).first().id}"
            blocks.append(
                {
                    "type": "section",
                    "block_id": str(i.id),
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{self.personalize(i.resource.name)}*",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": action_text},
                        "value": value,
                    },
                }
            )
        return blocks

    def format_intro_block(self, intro):
        text = f"*{intro.name}:*{intro.intro_person.full_name}\n"
        if intro.intro_person.position != "":
            text += f"{intro.intro_person.position}\n"
        if intro.intro_person.message != "":
            text += f"_{self.personalize(intro.intro_person.message)}_\n"
        text += intro.intro_person.email + " "
        if intro.intro_person.phone != "":
            text += intro.intro_person.phone
        block = {"type": "section", "text": {"type": "mrkdwn", "text": text}}
        if intro.intro_person.profile_image is not None:
            block["accessory"] = {
                "type": "image",
                "image_url": intro.intro_person.profile_image.get_url(),
                "alt_text": "profile image",
            }
        return block

    def open_modal(
        self, trigger_id, title, blocks, callback, private_metadata, submit_name
    ):
        if submit_name is None:
            submit_name = "Done"
        view = {
            "type": "modal",
            "callback_id": callback,
            "title": {
                "type": "plain_text",
                "text": title if len(title) < 24 else title[:20] + "...",
            },
            "submit": {"type": "plain_text", "text": submit_name},
            "blocks": blocks,
            "private_metadata": private_metadata,
        }
        self.client.views_open(trigger_id=trigger_id, view=view)

    def send_sequence_triggers(self, items, to_do_user):
        from users.models import ToDoUser

        blocks = []
        if len(items["introductions"]):
            for i in items["introductions"]:
                blocks.append(
                    self.format_intro_block(Introduction.objects.get(id=i.id))
                )
            self.send_message(blocks=blocks)
        for badge in items["badges"]:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _("*Congrats, you unlocked: %(item_name)s *")
                        % {"item_name": self.personalize(badge.name)},
                    },
                }
            ]
            blocks.append(badge.content.to_slack_block(self.user_obj))
            self.send_message(blocks=blocks)
        if len(items["to_do"]):
            to_do = [
                ToDoUser.objects.get(user=self.user_obj, to_do=i)
                for i in items["to_do"]
            ]
            if len(items["to_do"]) > 1:
                pre_message = _("We have just added these new to do items:")
            else:
                pre_message = _("We have just added a new to do item for you:")
            blocks = self.format_to_do_block(pre_message=pre_message, items=to_do)
            self.send_message(blocks=blocks)
        # send response from to do item back to channel
        if to_do_user is not None and to_do_user.to_do.send_back:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _(
                            "*Our new hire %(name)s just answered some questions:*"
                        )
                        % {"name": to_do_user.user.first_name},
                    },
                },
                {"type": "divider"},
            ]
            for i in to_do_user.form:
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{i['text']}*\n{i['value']}",
                        },
                    }
                )
            self.send_message(blocks=blocks, channel=to_do_user.to_do.channel)

    def create_buttons(self, categories):
        blocks = []
        if len(categories) == 0:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": _("No resources available")},
                }
            )
        for i in categories:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": i["name"]},
                            "value": f"category:{i['id']}",
                            "action_id": f"category:{i['id']}",
                        }
                    ],
                }
            )
        return blocks

    def format_account_approval_approval(self, user, user_id):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _(
                        "Would you like to put this new hire through onboarding?\n*Name:* %(name)s "
                    )
                    % {"name": user["profile"]["real_name"]},
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": _("Yeah!")},
                        "style": "primary",
                        "value": f"create:newhire:approve:{user_id}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": _("Nope")},
                        "style": "danger",
                        "value": f"create:newhire:deny:{user_id}",
                    },
                ],
            },
        ]
        return blocks

    def create_updated_view(self, value, view, course_completed):
        chapter = Chapter.objects.get(id=value)
        blocks = []
        if course_completed or (
            view["blocks"][0]["type"] == "select_static" and not chapter.type == 2
        ):
            blocks = [view["blocks"][0]]
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{chapter.name}*"},
            }
        )
        blocks.append(chapter.to_slack_block(self.user_obj))
        view["blocks"] = blocks
        del view["team_id"]
        del view["state"]
        del view["hash"]
        del view["previous_view_id"]
        del view["root_view_id"]
        del view["app_id"]
        del view["app_installed_team_id"]
        del view["bot_id"]
        del view["id"]
        view["callback_id"] = (
            view["callback_id"].rsplit(":", 1)[0] + ":" + str(chapter.id)
        )
        view["close"] = {"type": "plain_text", "text": _("Close"), "emoji": True}
        return view

    def help(self):
        messages = [
            _("Happy to help! Here are all the things you can say to me: \n\n"),
            _(
                "*What do I need to do today?*\nThis will show all the tasks you need to do today. I will show you these every day as well, but just incase you want to get them again."
            ),
            _(
                "*Do I have any to do items that are overdue?*\nThis will show all tasks that should have been completed. Please do those as soon as possible."
            ),
            _("*Show me all to do items*\nThis will show all tasks"),
            _("*Show me all resources*\nThis will show all resources."),
        ]

        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": item},
            }
            for item in messages
        ]
        self.send_message(blocks=blocks)
