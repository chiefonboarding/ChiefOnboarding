# misc items
from django.utils.translation import gettext as _

from admin.sequences.models import Sequence


def get_new_hire_approve_sequence_options():
    return {
        "type": "input",
        "block_id": "seq",
        "label": {
            "type": "plain_text",
            "text": _("Select sequences"),
        },
        "element": {
            "type": "multi_static_select",
            "placeholder": {
                "type": "plain_text",
                "text": _("Select sequences"),
            },
            "options": [
                {
                    "text": {"type": "plain_text", "text": seq.name},
                    "value": str(seq.id),
                }
                # max is 100 as per Slack limits
                for seq in Sequence.objects.all()[:100]
            ],
            "action_id": "answers",
        },
    }


def welcome_new_hire():
    return {
        "block_id": "input",
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "multiline": True,
            "action_id": "message",
        },
        "label": {
            "type": "plain_text",
            "text": _("What would you like to say to our new hire?"),
        },
    }


def get_new_hire_first_message_buttons():
    return [
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
                    "action_id": "show_to_do_items",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": _("Resources"),
                    },
                    "action_id": "show_resource_items",
                },
            ],
        },
    ]
