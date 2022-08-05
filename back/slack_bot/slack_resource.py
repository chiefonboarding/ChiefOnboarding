import json

from django.db.models import Count
from django.utils.translation import gettext as _

from admin.resources.models import Category

from .utils import actions, button, paragraph


class SlackResource:
    def __init__(self, resource_user, user):
        self.resource_user = resource_user
        self.resource = resource_user.resource
        self.user = user

    def get_block(self):
        if self.resource_user.is_course:
            action_text = _("View course")
        else:
            action_text = _("View resource")
        action_id = f"dialog:resource:{self.resource_user.id}"

        value = str(self.resource_user.id)
        return {
            "type": "section",
            "block_id": str(self.resource_user.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{self.user.personalize(self.resource.name)}*",
            },
            "accessory": button(action_text, "primary", value, action_id),
        }

    def get_chapters_menu(self):
        return {
            "type": "actions",
            "block_id": "change_resource_page",
            "elements": [
                {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": _("Select chapter"),
                        "emoji": True,
                    },
                    "options": [
                        chapter.slack_menu_item()
                        for chapter in self.resource_user.resource.chapters.exclude(
                            type=2
                        )
                    ],
                    "action_id": "change_resource_page",
                }
            ],
        }

    def modal_view(self, chapter_id):
        blocks = []
        if (
            not self.resource_user.is_course
            and self.resource_user.resource.chapters.filter(type=0).count() > 1
        ):
            # Create menu with chapters, exclude all question forms and folders
            blocks.append(
                SlackResource(self.resource_user, self.user).get_chapters_menu()
            )

        chapter = self.resource_user.resource.chapters.filter(id=chapter_id).first()

        # Add chapter title
        blocks.append(paragraph(f"*{chapter.name}*"))

        # Add content
        blocks = [*blocks, *chapter.to_slack_block(self.user)]

        private_metadata = {
            "current_chapter": chapter.id,
            "resource_user": self.resource_user.id,
        }
        modal = {
            "type": "modal",
            "callback_id": "dialog:resource",
            "title": {
                "type": "plain_text",
                "text": _("Course") if self.resource_user.is_course else _("Resource"),
            },
            "blocks": blocks,
            "private_metadata": json.dumps(private_metadata),
        }

        if (
            self.resource_user.is_course
            and self.resource_user.resource.chapters.count() > 1
        ):
            modal["submit"] = {"type": "plain_text", "text": _("Next")}

        return modal


class SlackResourceCategory:
    def __init__(self, user):
        self.user = user

    def category_buttons(self):

        categories = (
            Category.objects.annotate(resource_amount=Count("resource"))
            .exclude(resource_amount=0)
            .filter(resource__id__in=self.user.resources.values_list("id", flat=True))
        )

        if (
            len(categories) == 0
            and not self.user.resources.filter(category__isnull=True).exists()
        ):
            return [paragraph(_("No resources available"))]

        buttons = []
        if self.user.resources.filter(category__isnull=True).exists():
            buttons = [button(_("No category"), "primary", "-1", "category:-1")]
        for i in categories:
            buttons.append(button(i.name, "primary", f"{i.id}", f"category:{i.id}"))
        blocks = [paragraph(_("Select a category:")), actions(buttons)]
        return blocks
