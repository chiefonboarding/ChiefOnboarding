from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from admin.sequences.models import Sequence
from organization.models import Organization

from .utils import Slack, actions, button, paragraph

"""
Example payload:
{
    "type": "team_join",
    "user": {
        "id": "U0XXX",
        "name": "John",
        "deleted": false,
        "color": "9f34e7",
        "profile": {
            "first_name": "John",
            "last_name": "Do",
            "real_name": "John Do",
            "email": "john@chiefonboarding.com"
        },
        "is_admin": true,
        "is_owner": true,
        "is_primary_owner": true,
        "is_restricted": false,
        "is_ultra_restricted": false,
        "has_2fa": false,
        "two_factor_type": "sms",
        "tz": "UTC"
    }
}
"""


class SlackJoin:
    def __init__(self, payload):
        self.payload = payload
        self.org = Organization.object.get()
        self.user = None

    def get_user(self):
        return get_user_model().objects.filter(email__iexact=self.get_email())

    def get_first_name(self):
        profile = self.payload["user"]["profile"]
        if "first_name" in profile:
            return self.payload["user"]["profile"]["first_name"]

        if "real_name" in profile:
            return profile["real_name"].split(" ")[0]

        return ""

    def get_email(self):
        return self.payload["user"]["profile"]["email"]

    def get_timezone(self):
        return self.payload["user"]["tz"]

    def get_last_name(self):
        profile = self.payload["user"]["profile"]
        if "last_name" in profile:
            return self.payload["user"]["profile"]["last_name"]

        if "real_name" in profile:
            names = profile["real_name"].split(" ")[0]
            if len(names) > 1:
                return names[1]

        return ""

    def create_or_get_user(self):
        if self.get_user.exists():
            return self.get_user.first()
        else:
            return get_user_model().objects.create_new_hire(
                first_name=self.get_first_name(),
                last_name=self.get_last_name(),
                email=self.get_email(),
                password=get_user_model().set_unusable_password(),
                is_active=False,
                timezone=self.get_timezone(),
                start_day=datetime.now().today(),
            )

    def create_new_hire_or_ask_permission(self):
        user = self.create_or_get_user()
        # if no permissions are needed, then set user up as new hire
        if self.org.create_new_hire_without_confirm:
            user.role = 0
            user.save()
            # adding default sequences
            user.add_sequences(Sequence.objects.filter(auto_add=True))
            # scheduled tasks will pick it up from here
        else:
            # needs approval for new hire account
            blocks = self.request_create_new_hire_approval_blocks(user)
            Slack().send_message(
                blocks=blocks, channel=self.org.slack_confirm_person.slack_channel_id
            )

    def request_create_new_hire_approval_blocks(self, user):
        return [
            paragraph(
                _(
                    "Would you like to put this new hire "
                    "through onboarding?\n*Name:* %(name)s "
                )
                % {"name": user.full_name}
            ),
            actions(
                [
                    button(
                        _("Yeah!"), "primary", str(user.id), "create:newhire:approve"
                    ),
                    button(_("Nope"), "danger", "-1", "create:newhire:deny"),
                ]
            ),
        ]
