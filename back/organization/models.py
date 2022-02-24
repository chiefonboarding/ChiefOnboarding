from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.utils.functional import cached_property
from django.db import models
from django.utils.translation import gettext_lazy as _

from misc.models import File
from django.urls import reverse
from misc.urlparser import URLParser


class ObjectManager(models.Manager):
    def get(self):
        return self.get_queryset().first()


class Organization(models.Model):
    name = models.CharField(verbose_name=_("Name"),max_length=500)
    language = models.CharField(verbose_name=_("Language"),default="en", max_length=10, choices=settings.LANGUAGES)
    timezone = models.CharField(verbose_name=_("Timezone"),default="UTC", max_length=1000)

    # customization
    base_color = models.CharField(verbose_name=_("Base color"),max_length=10, default="#99835C")
    accent_color = models.CharField(verbose_name=_("Accent color"),max_length=10, default="#ffbb42")
    bot_color = models.CharField(verbose_name=_("Bot color"),max_length=10, default="#ffbb42")
    logo = models.ForeignKey(File, verbose_name=_("Logo"),on_delete=models.CASCADE, null=True)

    # login options
    credentials_login = models.BooleanField(verbose_name=_("Allow users to login with their username and password"),default=True)
    google_login = models.BooleanField(verbose_name=_("Allow users to login with their Google account"),default=False)
    slack_login = models.BooleanField(verbose_name=_("Allow users to login with their Slack account"),default=False)

    # additional settings
    new_hire_email = models.BooleanField(
        verbose_name=_("Send email to new hire with login credentials"),
        help_text=_(
            "This is essential if you want your new hires to login to the dashboard (disable if using Slack)"
        ),
        default=True,
    )
    new_hire_email_reminders = models.BooleanField(
        verbose_name=_("Send email to new hire with updates"),
        help_text=_("Think of new tasks that got assigned, new resources, badges... "),
        default=True,
    )
    new_hire_email_overdue_reminders = models.BooleanField(
        verbose_name=_("Send email to new hire when tasks are overdue"),
        help_text=_("These are daily emails, until all overdue tasks are completed."),
        default=False,
    )

    # Slack specific
    slack_buttons = models.BooleanField(
        verbose_name=_(
            "Add 'todo' and 'resource' buttons to the first message that's being sent to the new hire."
        ),
        help_text="Slack only",
        default=True,
    )
    ask_colleague_welcome_message = models.BooleanField(
        verbose_name=_(
            "Send a Slack message to the team to collect personal welcome messages from colleages."
        ),
        help_text=_("Slack only"),
        default=True,
    )
    send_new_hire_start_reminder = models.BooleanField(
        verbose_name=_(
            "Send a Slack message to the team on the day the new hire starts"
        ),
        help_text=_("Slack only"),
        default=False,
    )
    auto_create_user = models.BooleanField(
        verbose_name=_("Create a new hire when they join your Slack team"),
        help_text=_("If the user does not exist yet - Slack only"),
        default=False,
    )
    create_new_hire_without_confirm = models.BooleanField(
        verbose_name=_("Create new hires without needing confirm from a user"),
        help_text=_("Slack only"),
        default=False,
    )
    slack_confirm_person = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User to sent new hire account requests to"),null=True, on_delete=models.SET_NULL,
        help_text=_("Slack only"),
    )
    slack_default_channel = models.ForeignKey(
        "slack_bot.SlackChannel", verbose_name=_("This is the default channel where the bot will post messages in"),null=True, on_delete=models.SET_NULL,
        help_text=_("Slack only"),
    )

    object = ObjectManager()
    objects = models.Manager()

    def get_logo_url(self):
        # Check if cache option already exists AND the logo name is in the url
        # If the latter is not the case, then the logo changed and cache should refresh
        if cache.get("logo_url", None) is None or self.logo.name not in cache.get(
            "logo_url"
        ):
            cache.set("logo_url", self.logo.get_url(), 3500)
        return cache.get("logo_url")


class Tag(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class WelcomeMessage(models.Model):
    MESSAGE_TYPE = (
        (0, _("pre-boarding")),
        (1, _("new hire welcome")),
        (2, _("text welcome")),
        (3, _("slack welcome")),
        (4, _("slack knowledge")),
    )

    message = models.CharField(verbose_name=_("Message"), max_length=20250, blank=True)
    language = models.CharField(choices=settings.LANGUAGES, max_length=3, default="en")
    message_type = models.IntegerField(choices=MESSAGE_TYPE, default=0)


class TemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(template=True)


class BaseItem(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=240)
    tags = ArrayField(models.CharField(max_length=10200), verbose_name=_("Tags"), blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    template = models.BooleanField(default=True)

    objects = models.Manager()
    templates = TemplateManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.tags is None:
            self.tags = []
        else:
            for i in self.tags:
                if i != "":
                    Tag.objects.get_or_create(name=i)
        super(BaseItem, self).save(*args, **kwargs)

    def class_name(self):
        return self.__class__.__name__

    def duplicate(self):
        self.pk = None
        self.name = _("%(name)s (duplicate)") % {"name": self.name}
        self.save()
        return self

    def _prep_inner_text_for_slack(self, text):
        replacements = (
            ("<p>", ""),
            ("</p>", ""),
            ("<br>", ""),
            ("<br />", ""),
            ("<b>", "*"),
            ("</b>", "*"),
            ("<strong>", "*"),
            ("</strong>", "*"),
            ("</i>", "_"),
            ("<i>", "_"),
            ("<em>", "_"),
            ("</em>", "_"),
            ("<u>", ""),
            ("</u>", ""),
            ("<code>", "`"),
            ("</code>", "`"),
            ("</strike>", "~"),
            ("<strike>", "~"),
        )
        for r in replacements:
            text = text.replace(*r)
            parser = URLParser()
            parser.feed(content)
            for link in parser.get_links():
                text = text.replace(
                    link["original_tag"] + link["text"] + "</a>",
                    "<" + link["url"] + "|" + link["text"] + ">")
        return text


    def to_slack_block(self, user):
        blocks = self.content.blocks
        slack_blocks = []
        for item in blocks:
            if 'text' in item.data:
                if item.data.text == "":
                    item.data.text = "-"
                text = user.personalize(item.data.text)
                item.data.text = self._prep_inner_text_for_slack(text)
            if 'items' in item.data:
                for list_item in item.data.items:
                    if list_item == "":
                        list_item = "-"
                    text = user.personalize(list_item)
                    item.data.text = self._prep_inner_text_for_slack(text)
            slack_block = {"type": "section", "text": {"type": "mrkdwn", "text": item.data.text}}
            if item.type == "header":
                slack_block["text"]["text"] = "*" + item.data.text + "*"
            elif item.type == "quote":
                slack_block = {
                    "type": "context",
                    "elements": {"text": {"type": "mrkdwn", "text": item.data.text + "\n" + item.data.caption }},
                }
            elif item.type == "list" and item.data.style == "ordered":
                ul_list = ""
                for idx, list_item in enumerate(item.data.items):
                    ul_list += str(idx + 1) + ". " + user.personalize(list_item) + "\n"
                slack_block["text"]["text"] = ul_list
            elif item.type == "list" and item.data.style == "unordered":
                ol_list = ""
                for list_item in item.data.items:
                    ol_list += "* " + user.personalize(list_item) + "\n"
                slack_block["text"]["text"] = ol_list
            elif item.type == "delimiter":
                return {"type": "divider"}
            elif item.type == "file":
                files_text = "<" + self.files[0].get_url() + "|Watch video>"
                slack_block["text"]["text"] = files_text
            elif item.type == "video":
                files_text = "<" + File.objects.get(id=item["file"]["id"]).get_url() + "|" + item["file"]["name"] + "> "
                slack_block["text"]["text"] = files_text
            elif item.type == "image":
                slack_block = {
                    "type": "image",
                    "image_url": File.objects.get(id=item["file"]["id"]).get_url(),
                    "alt_text": "image",
                }
            elif item.type == "question":
                options = []
                for i in item.items:
                    options.append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": user.personalize(i["text"]),
                                "emoji": True,
                            },
                            "value": i["id"],
                        }
                    )
                slack_block = {
                    "type": "input",
                    "block_id": str(item.id),
                    "element": {
                        "type": "static_select",
                        "action_id": str(item.id),
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select answer",
                            "emoji": True,
                        },
                        "options": options,
                    },
                    "label": {"type": "plain_text", "text": item.data.text, "emoji": True},
                }
            slack_blocks.append(slack_block)
        return slack_blocks

class Changelog(models.Model):
    added = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField(default="")

    class Meta:
        ordering = ["-id"]


NOTIFICATION_TYPES = [
    ("added_todo", _("A new to do item has been added")),
    ("completed_todo", _("To do item has been marked as completed")),
    ("added_resource", _("A new resource item has been added")),
    ("completed_course", _("Course has been completed")),
    ("added_badge", _("A new badge item has been added")),
    ("added_introduction", _("A new introduction item has been added")),
    ("added_preboarding", _("A new preboarding item has been added")),
    ("added_new_hire", _("A new hire has been added")),
    ("added_administrator", _("A new administrator has been added")),
    ("added_admin_task", _("A new admin task has been added")),
    ("sent_email_message", _("A new email has been sent")),
    ("sent_text_message", _("A new text message has been sent")),
    ("sent_slack_message", _("A new slack message has been sent")),
    ("failed_no_phone", _("Couldn't sent text message: number is missing")),
]


class Notification(models.Model):
    notification_type = models.CharField(
        choices=NOTIFICATION_TYPES, max_length=100, default="added_todo"
    )
    extra_text = models.TextField(default="")
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="notification_owners",
    )
    created_for = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="notification_receivers",
    )
    public_to_new_hire = models.BooleanField(default=False)
    reverse_link = models.CharField(max_length=200, default="")
    reverse_link_params = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created"]

    @cached_property
    def full_link(self):
        if self.reverse_link == "":
            return ""
        return reverse(self.reverse_link, kwargs=self.reverse_link_params)

    @cached_property
    def has_not_seen(self):
        if self.created_for is None:
            return False

        return self.created_for.seen_updates < self.created
