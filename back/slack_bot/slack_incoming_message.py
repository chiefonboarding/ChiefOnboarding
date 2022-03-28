from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from admin.resources.models import Resource
from admin.to_do.models import ToDo
from organization.models import Organization
from users.models import ToDoUser

from .slack_resource import SlackResource, SlackResourceCategory
from .slack_to_do import SlackToDo
from .utils import Slack, has_slack_account, paragraph

"""
Example payload:
{
    "token": "xxxxxx",
    "team_id": "T061EG3I6",
    "api_app_id": "A0P343K2",
    "event": {
        "type": "message",
        "channel": "D0243491L",
        "user": "U2147483497",
        "text": "show me to do items",
        "ts": "1355514523.000005",
        "event_ts": "133417523.000005",
        "channel_type": "im"
    },
    "type": "event_callback",
    "authed_teams": [
        "T061349R6"
    ],
    "event_id": "Ev0P342K21",
    "event_time": 13553437523
}
"""


class SlackIncomingMessage:
    def __init__(self, payload):
        self.payload = payload
        self.org = Organization.object.get()
        self.user = (
            get_user_model()
            .objects.filter(slack_user_id=self.payload["event"]["user"])
            .first()
        )
        self.message = self.payload["event"]["text"]

    def user_exists(self):
        return self.user is not None

    def is_request_for_to_do(self):
        return _("to do") in self.message

    def is_request_for_resources(self):
        return _("resources") in self.message

    def is_request_for_help(self):
        return _("help") in self.message

    def reply_with_search_results(self):
        items = Resource.objects.search(self.user, self.message)
        results = [SlackResource(task, self.user).resource_block() for task in items]

        text = (
            _("Here is what I found: ")
            if items.count() > 0
            else _("Unfortunately, I couldn't find anything.")
        )
        return [paragraph(text), results]

    def reply_with_resource_categories(self):
        # show categories (buttons)
        return SlackResourceCategory(user=self.user).category_button()

    def reply_with_help_options(self):
        messages = [
            _("Happy to help! Here are all the things you can say to me: \n\n"),
            _(
                "*What do I need to do today?*\nThis will show all the tasks you need to do today. "
                "I will show you these every day as well, but just incase you want to get them again."
            ),
            _(
                "*Do I have any to do items that are overdue?*\nThis will show all "
                "tasks that should have been completed. Please do those as soon as possible."
            ),
            _("*Show me all to do items*\nThis will show all tasks"),
            _("*Show me all resources*\nThis will show all resources."),
        ]

        return [paragraph(item) for item in messages]

    def reply_with_to_do_items(self):
        items = ToDoUser.objects.all_to_do(self.user)
        if _("today") in self.message:
            items = ToDoUser.objects.due_today(self.user)
        if _("overdue") in self.message:
            items = ToDoUser.objects.overdue(self.user)

        tasks = [SlackToDo(task.to_do, self.user).to_do_block() for task in items]

        text = (
            _("These are the tasks you need to complete:")
            if len(tasks)
            else _("I couldn't find any tasks.")
        )

        return [paragraph(text), tasks]

    def reply_request_access_supervisor(self):
        return [
            paragraph(
                _(
                    "You don't seem to be setup yet. Please ask your supervisor for"
                    " access."
                )
            )
        ]
