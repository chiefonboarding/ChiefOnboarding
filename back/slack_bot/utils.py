import slack_sdk
from django.conf import settings
from django.core.cache import cache

from admin.integrations.models import Integration


class Slack:
    def __init__(self):
        if not settings.FAKE_SLACK_API:
            try:
                team = Integration.objects.get(integration=0)
                self.client = slack_sdk.WebClient(token=team.token)
            except Integration.DoesNotExist:
                if settings.SLACK_BOT_TOKEN != "":
                    self.client = slack_sdk.WebClient(token=settings.SLACK_BOT_TOKEN)
                raise Exception("Access token not available")

    def get_channels(self):
        try:
            response = self.client.api_call(
                "conversations.list",
                data={
                    "exclude_archived": True,
                    "types": "public_channel,private_channel",
                },
            )
        except Exception:
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

    def update_message(self, text="", blocks=[], channel="", ts=0):
        # if there is no channel, then drop
        if channel == "" or ts == 0:
            return False

        if settings.FAKE_SLACK_API:
            cache.set("slack_channel", channel)
            cache.set("slack_ts", ts)
            cache.set("slack_blocks", blocks)
            cache.set("slack_text", text)
            return

        return self.client.chat_update(
            channel=channel,
            ts=ts,
            text=text,
            blocks=blocks,
        )

    def send_ephemeral_message(self, user, blocks=[], channel="", text=""):
        # if there is no channel, then drop
        if channel == "":
            return False

        if settings.FAKE_SLACK_API:
            cache.set("slack_channel", channel)
            cache.set("slack_blocks", blocks)
            cache.set("slack_text", text)
            return {"channel": "slacky"}

        return self.client.chat_postEphemeral(
            channel=channel, user=user, text=text, blocks=blocks
        )

    def send_message(self, blocks=[], channel="", text=""):
        # if there is no channel, then drop
        if channel == "":
            return False

        if settings.FAKE_SLACK_API:
            cache.set("slack_channel", channel)
            cache.set("slack_blocks", blocks)
            cache.set("slack_text", text)
            return {"channel": "slacky"}

        return self.client.chat_postMessage(channel=channel, text=text, blocks=blocks)

    def open_modal(self, trigger_id, view):
        if settings.FAKE_SLACK_API:
            cache.set("slack_trigger_id", trigger_id)
            cache.set("slack_view", view)
            return

        return self.client.views_open(trigger_id=trigger_id, view=view)

    def update_modal(self, view_id, hash, view):
        if settings.FAKE_SLACK_API:
            cache.set("slack_view_id", view_id)
            cache.set("slack_view", view)
            return

        return self.client.views_update(view_id=view_id, hash=hash, view=view)


def paragraph(text):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def actions(elements=[]):
    return {"type": "actions", "elements": elements}


def button(text, style, value, action_id):
    return {
        "type": "button",
        "text": {"type": "plain_text", "text": text},
        "style": style,
        "value": value,
        "action_id": action_id,
    }
