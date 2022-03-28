import slack_sdk as slack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.utils import translation
from django.utils.translation import gettext as _

from admin.integrations.models import AccessToken
from admin.introductions.models import Introduction
from admin.resources.models import Chapter
from organization.models import Organization


class Slack:

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
