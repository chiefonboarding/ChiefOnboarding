from django.conf import settings
from django.utils.translation import gettext as _

from users.models import ToDoUser

from .slack_modal import SlackModal
from .utils import button, paragraph


class SlackToDo:
    def __init__(self, to_do, user):
        self.to_do = to_do
        self.user = user

    def footer_text(self):
        workday = self.user.workday
        if self.to_do.due_on_day == 0:
            return _("This task has no deadline.")
        if (self.to_do.due_on_day - workday) < 0:
            return _("This task is overdue")
        if (self.to_do.due_on_day - workday) == 0:
            return _("This task is due today")
        return _("This task needs to be completed in %(amount)s working days") % {
            "amount": str(self.to_do.due_on_day - workday)
        }

    def get_complete_button(self):
        if self.to_do.inline_slack_form:
            value = "dialog:to_do:" + str(self.to_do.id)
            action_text = _("View details")
        else:
            value = "to_do:external:" + str(self.to_do.id)
            action_text = _("Mark completed")

        return button(action_text, "primary", value)

    def to_do_block(self):
        if self.to_do.inline_slack_form:
            text = f"*{self.user.personalize(self.to_do.name)}*\n{self.footer_text()}"
        else:
            text = (
                f"*{self.user.personalize(self.to_do.name)}* "
                + f"<{settings.BASE_URL}/#/slackform?"
                + f"token={self.user.unique_url}&id={str(self.to_do.id)}|"
                + _("View details")
                + f">\n{self.footer_text()}"
            )
        return {
            "type": "section",
            "block_id": str(self.to_do.id),
            "text": {"type": "mrkdwn", "text": text},
            "accessory": self.get_complete_button(),
        }

    def create_modal_view(self, ids, text, ts):
        blocks = self.to_do.to_slack_block()
        private_metadata = {
            # We are removing the first block as that's the message
            # "These are the to do items you have to complete....".
            # We only need the action block ids from the todo items
            "to_do_ids_from_original_message": ids[1:],
            "text": text,
            "to_do_id": self.to_do.id,
            "message_ts": ts,
        }
        return SlackModal().create_view(
            title=self.to_do.name,
            blocks=blocks,
            callback="complete:to_do",
            private_metadata=str(private_metadata),
        )

    def not_completed_message(self):
        return paragraph(
            _(
                "Please complete the form first. Click on 'View details' to "
                "complete it."
            )
        )


class SlackToDoManager:
    def __init__(self, user, to_dos=None):
        self.to_dos = to_dos
        self.user = user

    def get_blocks(self, ids, remove_id=None, text=""):

        if remove_id is not None:
            ids = ids.remove(remove_id)

        items = ToDoUser.objects.filter(id__in=ids)
        tasks = [SlackToDo(task.to_do, self.user).to_do_block() for task in items]

        if text == "":
            text = (
                _("These are the tasks you need to complete:")
                if len(tasks)
                else _("I couldn't find any tasks.")
            )

        return [paragraph(text), *tasks]
