from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from misc.mixins import ContentMixin
from misc.models import File


class ObjectManager(models.Manager):
    def get(self):
        return self.get_queryset().first()


class Organization(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=500)
    language = models.CharField(
        verbose_name=_("Language"),
        default="en",
        max_length=10,
        choices=settings.LANGUAGES,
    )
    timezone = models.CharField(
        verbose_name=_("Timezone"),
        default="UTC",
        max_length=1000,
        choices=[(x, x) for x in pytz.common_timezones],
    )

    # customization
    base_color = models.CharField(
        verbose_name=_("Base color"), max_length=10, default="#99835C"
    )
    accent_color = models.CharField(
        verbose_name=_("Accent color"), max_length=10, default="#ffbb42"
    )
    bot_color = models.CharField(
        verbose_name=_("Bot color"), max_length=10, default="#ffbb42"
    )
    logo = models.ForeignKey(
        File, verbose_name=_("Logo"), on_delete=models.CASCADE, null=True
    )

    # login options
    credentials_login = models.BooleanField(
        verbose_name=_("Allow users to login with their username and password"),
        default=True,
    )
    google_login = models.BooleanField(
        verbose_name=_("Allow users to login with their Google account"), default=False
    )
    slack_login = models.BooleanField(
        verbose_name=_("Allow users to login with their Slack account"), default=False
    )

    # additional settings
    new_hire_email = models.BooleanField(
        verbose_name=_("Send email to new hire with login credentials"),
        help_text=_(
            "This is essential if you want your new hires to login to the dashboard "
            "(disable if using Slack)"
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
            "Add 'todo' and 'resource' buttons to the first message that's being sent "
            "to the new hire."
        ),
        default=True,
    )
    ask_colleague_welcome_message = models.BooleanField(
        verbose_name=_(
            "Send a Slack message to the team to collect personal welcome messages from"
            " colleages."
        ),
        default=True,
    )
    send_new_hire_start_reminder = models.BooleanField(
        verbose_name=_(
            "Send a Slack message to the team on the day the new hire starts"
        ),
        default=False,
    )
    auto_create_user = models.BooleanField(
        verbose_name=_("Create a new hire when they join your Slack team"),
        help_text=_("If the user does not exist yet"),
        default=False,
    )
    create_new_hire_without_confirm = models.BooleanField(
        verbose_name=_("Create new hires without needing confirm from a user"),
        default=False,
    )
    slack_confirm_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User to sent new hire account requests to"),
        null=True,
        on_delete=models.SET_NULL,
    )
    slack_default_channel = models.ForeignKey(
        "slack_bot.SlackChannel",
        verbose_name=_(
            "This is the default channel where the bot will post messages in"
        ),
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    slack_birthday_wishes_channel = models.ForeignKey(
        "slack_bot.SlackChannel",
        verbose_name=_(
            "This is the channel where the bot will send birthday wishes in. ",
        ),
        help_text=_(
            "Leave blank to disable this. Timing is based on when this was enabled."
        ),
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Field to determine if there has been an outage and tasks need to be caught up
    timed_triggers_last_check = models.DateTimeField(auto_now_add=True)
    custom_email_template = models.TextField(
        default="",
        verbose_name=_("Base email template"),
        help_text=_(
            "Leave blank to use the default one. "
            "See documentation if you want to use your own."
        ),
    )

    object = ObjectManager()
    objects = models.Manager()

    @property
    def base_color_rgb(self):
        base_color = self.base_color.strip("#")
        b_c_t = tuple(int(base_color[i : i + 2], 16) for i in (0, 2, 4))  # noqa
        return "%s, %s, %s" % b_c_t

    @property
    def accent_color_rgb(self):
        accent_color = self.accent_color.strip("#")
        return tuple(int(accent_color[i : i + 2], 16) for i in (0, 2, 4))  # noqa

    @property
    def current_datetime(self):
        local_tz = pytz.timezone("UTC")
        us_tz = pytz.timezone(self.timezone)
        local = local_tz.localize(datetime.now())
        return us_tz.normalize(local.astimezone(us_tz))

    def create_email(self, context):
        if self.custom_email_template == "":
            return render_to_string("email/base.html", context)
        else:
            t = Template(self.custom_email_template)
            return t.render(Context(context))

    @cached_property
    def get_logo_url(self):
        if self.logo is None:
            return ""

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

    def defer_content(self):
        if "content" in self.model._meta.get_fields():
            return self.get_queryset().defer("content")
        return self.get_queryset()


class ObjectsManager(models.Manager):
    def defer_content(self):
        if "content" in super().model._meta.get_fields():
            return super().get_queryset().defer("content")
        return super().get_queryset()


class BaseItem(ContentMixin, models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=240)
    tags = ArrayField(
        models.CharField(max_length=10200), verbose_name=_("Tags"), blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    template = models.BooleanField(default=True)

    objects = ObjectsManager()
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

    def duplicate(self, change_name=True):
        self.pk = None
        if change_name:
            self.name = _("%(name)s (duplicate)") % {"name": self.name}
        self.save()
        return self

    @property
    def form_items(self):
        blocks = []
        for block in self.content["blocks"]:
            if (
                "data" in block
                and "type" in block["data"]
                and block["data"]["type"] in ["input", "text", "check", "upload"]
            ):
                blocks.append(block)
        return blocks


NOTIFICATION_TYPES = [
    ("added_todo", _("A new to do item has been added")),
    ("completed_todo", _("To do item has been marked as completed")),
    ("added_resource", _("A new resource item has been added")),
    ("completed_course", _("Course has been completed")),
    ("added_badge", _("A new badge item has been added")),
    ("added_introduction", _("A new introduction item has been added")),
    ("added_preboarding", _("A new preboarding item has been added")),
    ("added_appointment", _("A new appointment item has been added")),
    ("added_new_hire", _("A new hire has been added")),
    ("added_administrator", _("A new administrator has been added")),
    ("added_manager", _("A new manager has been added")),
    ("added_admin_task", _("A new admin task has been added")),
    ("sent_email_message", _("A new email has been sent")),
    ("sent_text_message", _("A new text message has been sent")),
    ("sent_slack_message", _("A new slack message has been sent")),
    ("updated_slack_message", _("A new slack message has been updated")),
    ("sent_email_login_credentials", _("Login credentials have been sent")),
    ("sent_email_task_reopened", _("Reopened task email has been sent")),
    ("sent_email_task_reminder", _("Task reminder email has been sent")),
    ("sent_email_new_hire_credentials", _("Sent new hire credentials email")),
    ("sent_email_preboarding_access", _("Sent new hire preboarding email")),
    ("sent_email_custom_sequence", _("Sent email from sequence")),
    ("sent_email_new_hire_with_updates", _("Sent email with updates to new hire")),
    ("sent_email_admin_task_extra", _("Sent email to extra person in admin task")),
    (
        "sent_email_admin_task_new_assigned",
        _("Sent email about new person assigned to admin task"),
    ),
    (
        "sent_email_admin_task_new_comment",
        _("Sent email about new comment on admin task"),
    ),
    (
        "sent_email_integration_notification",
        _("Sent email about completing integration call"),
    ),
    ("failed_no_phone", _("Couldn't send text message: number is missing")),
    ("failed_no_email", _("Couldn't send email message: email is missing")),
    (
        "failed_email_recipients_refused",
        _("Couldn't deliver email message: recipient refused"),
    ),
    ("failed_email_delivery", _("Couldn't deliver email message: provider error")),
    ("failed_email_address", _("Couldn't deliver email message: provider error")),
    ("failed_send_slack_message", _("Couldn't send Slack message")),
    ("failed_update_slack_message", _("Couldn't update Slack message")),
    ("ran_integration", _("Integration has been triggered")),
    ("failed_integration", _("Couldn't complete integration")),
    (
        "failed_text_integration_notification",
        _("Couldn't send integration notification"),
    ),
]


class Notification(models.Model):
    notification_type = models.CharField(
        choices=NOTIFICATION_TYPES, max_length=100, default="added_todo"
    )
    extra_text = models.TextField(default="")
    description = models.TextField(default="")
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
    item_id = models.IntegerField(null=True)
    notified_user = models.BooleanField(default=False)

    # Slack only
    blocks = models.JSONField(default=list)

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
