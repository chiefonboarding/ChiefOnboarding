import json

from django.conf import settings
from django.utils.translation import gettext as _

from users.models import ToDoUser

from .utils import button, paragraph


class SlackToDo:
    def __init__(self, to_do_user, user):
        self.to_do_user = to_do_user
        self.user = user

    def footer_text(self):
        workday = self.user.workday(self.to_do_user.base_date)
        if self.to_do_user.to_do.due_on_day == 0:
            return _("This task has no deadline.")
        if (self.to_do_user.to_do.due_on_day - workday) < 0:
            return _("This task is overdue")
        if (self.to_do_user.to_do.due_on_day - workday) == 0:
            return _("This task is due today")
        return _("This task needs to be completed in %(amount)s working days") % {
            "amount": str(self.to_do_user.to_do.due_on_day - workday)
        }

    def get_complete_button(self):
        if self.to_do_user.to_do.inline_slack_form:
            value = str(self.to_do_user.id)
            action_text = _("View details")
        else:
            value = str(self.to_do_user.id)
            action_text = _("Mark completed")

        action_id = "dialog:to_do:" + str(self.to_do_user.id)

        return button(action_text, "primary", value, action_id)

    def get_block(self):
        if self.to_do_user.to_do.inline_slack_form:
            text = (
                f"*{self.user.personalize(self.to_do_user.to_do.name)}*\n"
                f"{self.footer_text()}"
            )
        else:
            text = (
                f"*{self.user.personalize(self.to_do_user.to_do.name)}* "
                + f"<{settings.BASE_URL}/new_hire/slackform/"
                + f"{str(self.to_do_user.to_do.id)}/?"
                + f"token={self.user.unique_url}|"
                + _("View details")
                + f">\n{self.footer_text()}"
            )
        return {
            "type": "section",
            "block_id": str(self.to_do_user.id),
            "text": {"type": "mrkdwn", "text": text},
            "accessory": self.get_complete_button(),
        }

    def modal_view(self, ids, text, ts):
        blocks = self.to_do_user.to_do.to_slack_block(self.user)
        private_metadata = {
            # We are removing the first block as that's the message
            # "These are the to do items you have to complete....".
            # We only need the action block ids from the todo items
            "to_do_ids_from_original_message": ids[1:],
            "text": text,
            "to_do_id": self.to_do_user.id,
            "message_ts": ts,
        }
        title = self.to_do_user.to_do.name
        return {
            "type": "modal",
            "callback_id": "complete:to_do",
            "title": {
                "type": "plain_text",
                "text": title if len(title) < 24 else title[:20] + "...",
            },
            "submit": {"type": "plain_text", "text": _("done")},
            "blocks": blocks,
            "private_metadata": json.dumps(private_metadata),
        }


class SlackToDoManager:
    def __init__(self, user):
        self.user = user

    def get_blocks(self, ids, remove_id=None, text=""):
        if remove_id is not None:
            ids.remove(str(remove_id))

        items = ToDoUser.objects.filter(id__in=ids).order_by("id")
        tasks = [SlackToDo(task, self.user).get_block() for task in items]

        if text == "" or len(tasks) == 0:
            text = (
                _("These are the tasks you need to complete:")
                if len(tasks)
                else _("I couldn't find any tasks.")
            )

        return [paragraph(text), *tasks]
