from django.contrib.auth import get_user_model

from .slack_resource import SlackResourceCategory
from .slack_to_do import SlackToDoManager

"""
Example payload:

{
  "type": "block_actions",
  "team": {
    "id": "T9TK3CUXX",
    "domain": "example1"
  },
  "user": {
    "id": "UA8RXUXXL",
    "username": "stan",
    "team_id": "T9TK34KW"
  },
  "api_app_id": "AABA344CD",
  "token": "xxxx",
  "container": {
    "type": "message_attachment",
    "message_ts": "1548263411.000200",
    "attachment_id": 1,
    "channel_id": "CBR2V342X",
    "is_ephemeral": false,
    "is_app_unfurl": false
  },
  "trigger_id": "12321443423423.serk34.er3444443",
  "channel": {
    "id": "CBR2V342X",
    "name": "with-stan"
  },
  "message": {
    "bot_id": "BAH5CA34",
    "type": "message",
    "text": "This content can't be displayed.",
    "user": "UA34RU415",
    "ts": "1548234231.023333400",
    "blocks": []
    ...
  },
  "response_url": "https://hooks.slack.com/actions/343333/33432444/3r3423bosdk",
  "actions": [
    {
      "action_id": "348o341",
      "block_id": "=33411",
      "text": {
        "type": "plain_text",
        "text": "View",
        "emoji": true
      },
      "value": "resource:12",
      "type": "button",
      "action_ts": "34.34333333"
    }
  ]
}
"""


class SlackBlockAction:
    def __init__(self, payload):
        self.payload = payload
        self.user = None

    def get_user(self):
        # if user does not exist, it will return None
        self.user = (
            get_user_model()
            .objects.filter(slack_user_id=self.payload["user"]["id"])
            .first()
        )
        return self.user is not None

    def get_channel(self):
        return self.payload["channel"]["id"]

    def get_trigger_id(self):
        return self.payload["trigger_id"]

    def get_block_ids(self):
        if "blocks" not in self.payload["message"]:
            return []
        return [x["block_id"] for x in self.payload["message"]["blocks"]]

    def get_blocks(self):
        if "blocks" not in self.payload["message"]:
            return []
        return self.payload["message"]["blocks"]

    def get_timestamp_message(self):
        return self.payload["message"]["ts"]

    def get_action(self):
        if "actions" in self.payload:
            return self.payload["actions"][0]
        return False

    def get_action_value(self):
        if self.get_action() and "value" in self.get_action():
            return self.get_action()["value"]
        return False

    def is_change_resource_page(self):
        if self.get_action():
            return self.get_action()["block_id"] == "change_page"
        return False

    def is_type(self, type):
        if self.get_action_value():
            return type in self.get_action_value()
        return False

    def action_array(self):
        if self.get_action_value():
            return self.get_action_value().split(":")

    def reply_to_do_items(self):
        ids = ToDoUser.objects.all_to_do(self.user).values_list("id", flat=True)

        return SlackToDoManager(self.user).get_blocks(ids)

    def reply_with_resource_categories(self):
        # show categories (buttons)
        return SlackResourceCategory(user=self.user).category_button()
