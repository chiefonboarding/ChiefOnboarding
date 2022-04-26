from django.db.models import Count
from django.utils.translation import gettext as _

from admin.resources.models import Category

from .slack_modal import SlackModal
from .utils import actions, button, paragraph


class SlackResource:
    def __init__(self, resource_user, user):
        self.resource_user = resource_user
        self.resource = resource_user.resource
        self.user = user

    def get_block(self):
        first_chapter_id = self.resource.first_chapter_id
        if self.resource_user.is_course and not self.resource_user.completed_course:
            value = f"dialog:course:{self.resource_user.id}:{first_chapter_id}"
            action_text = _("View course")
        else:
            action_text = _("View resource")
            value = f"dialog:resource:{self.resource_user.id}:{first_chapter_id}"
        return {
            "type": "section",
            "block_id": str(self.resource_user.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{self.user.personalize(self.resource.name)}*",
            },
            "accessory": button(action_text, "primary", value),
        }

    def get_chapters_menu(self):
        return {
            "type": "actions",
            "block_id": "change_page",
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
                }
            ],
        }

    def modal_view(self, chapter_id):
        blocks = []
        if self.resource_user is None or self.resource_user.is_course:
            # Create menu with chapters
            blocks.append(
                SlackResource(self.resource_user, self.user).get_chapters_menu()
            )

        chapter = self.resource.next_chapter(chapter_id, self.resource_user.is_course)

        # Add chapter title
        blocks.append(paragraph(f"*{chapter.name}*"))

        # Add content
        blocks.append(chapter.content.to_slack_block(self.user))

        private_metadata = {
            "current_chapter": chapter.id,
            "resource_user": self.resource_user.id,
        }
        return SlackModal().create_view(
            title=_("Resource"),
            blocks=blocks,
            callback="dialog:resource",
            private_metadata=str(private_metadata),
            submit_name=_("Next"),
        )


class SlackResourceCategory:
    def __init__(self, user):
        self.user = user

    def category_button(self):

        categories = (
            Category.objects.annotate(resource_amount=Count("resource"))
            .exclude(resource_amount=0)
            .filter(
                resource_set__id__in=self.user.resources.values_list("id", flat=True)
            )
        )

        blocks = []
        if len(categories) == 0:
            return [paragraph(_("No resources available"))]
        if self.user.resources.filter(category__isnull=True).exists():
            blocks.append(
                actions(
                    button(_("No category"), "primary", "category:-1", "category:-1")
                )
            )
        for i in categories:
            blocks.append(
                actions(
                    button(
                        i["name"], "primary", f"category:{i['id']}", f"category:{i['id']}"
                    )
                )
            )
        return blocks
