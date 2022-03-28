from django.conf import settings
from django.utils.translation import gettext as _

from .slack_modal import SlackModal
from .utils import button, paragraph


class SlackIntro:
    def __init__(self, intro, user):
        self.intro = intro
        self.user = user

    def format_block(self):
        text = f"*{self.intro.name}:*{self.intro.intro_person.full_name}\n"
        if self.intro.intro_person.position != "":
            text += f"{self.intro.intro_person.position}\n"
        if self.intro.intro_person.message != "":
            text += f"_{self.user.personalize(self.intro.intro_person.message)}_\n"
        text += self.intro.intro_person.email + " "
        if self.intro.intro_person.phone != "":
            text += self.intro.intro_person.phone
        block = paragraph(text)
        if self.intro.intro_person.profile_image is not None:
            block["accessory"] = {
                "type": "image",
                "image_url": self.intro.intro_person.profile_image.get_url(),
                "alt_text": "profile image",
            }
        return block
