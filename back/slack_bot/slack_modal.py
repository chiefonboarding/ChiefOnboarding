import json

from django.contrib.auth import get_user_model

"""
Example payload:

{
   "title": {
      "type": "plain_text",
      "text": "Modal Title"
    },
    "submit": {
        "type": "plain_text",
        "text": "Submit"
    },
    "blocks": [
        {
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "sl_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Placeholder text for single-line input"
                }
            },
            "label": {
                "type": "plain_text",
                "text": "Label"
            },
            "hint": {
                "type": "plain_text",
                "text": "Hint text"
            }
        },
        {
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "ml_input",
                "multiline": true,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Placeholder text for multi-line input"
                }
            },
            "label": {
                "type": "plain_text",
                "text": "Label"
            },
            "hint": {
                "type": "plain_text",
                "text": "Hint text"
            }
        }
    ],
    "type": "modal"
}

"""


class SlackModal:
    def __init__(self, payload=None):
        if payload is not None:
            self.current_view = payload["current_view"]
            self.user_payload = payload["user"]
        self.user = None

    def get_user(self):
        # if user does not exist, it will return None
        self.user = (
            get_user_model()
            .objects.filter(slack_user_id=self.user_payload["id"])
            .first()
        )
        return self.user is not None

    def get_channel(self):
        return self.current_view["channel"]["id"]

    def get_callback_id(self):
        return self.current_view["callback_id"]

    def is_type(self, type):
        return self.get_callback_id() == type

    def get_filled_in_values(self):
        return self.current_view["state"]["values"]

    def get_private_metadata(self):
        try:
            return json.loads(self.current_view["private_metadata"])
        except ValueError:
            return self.current_view["private_metadata"]

    def create_view(self, title, blocks, callback, private_metadata, submit_name=None):
        if submit_name is None:
            submit_name = "Done"
        return {
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
