from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models
from django.db.models import CheckConstraint, Q
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
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
    oidc_login = models.BooleanField(
        verbose_name=_("Allow users to login with OIDC"), default=False
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

    class Meta:
        # a little hacky, but works fine to prevent multiple orgs
        constraints = [
            CheckConstraint(
                check=Q(id=1),
                name="only_one_allowed",
            ),
        ]

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
    class Type(models.IntegerChoices):
        PREBOARDING = 0, _("pre-boarding")
        NEWHIRE_WELCOME = 1, _("new hire welcome")
        TEXT_WELCOME = 2, _("text welcome")
        SLACK_WELCOME = 3, _("slack welcome")
        SLACK_KNOWLEDGE = 4, _("slack knowledge")

    message = models.CharField(verbose_name=_("Message"), max_length=20250, blank=True)
    language = models.CharField(choices=settings.LANGUAGES, max_length=3, default="en")
    message_type = models.IntegerField(choices=Type.choices, default=Type.PREBOARDING)


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


class Notification(models.Model):
    class Type(models.TextChoices):
        ADDED_TODO = "added_todo", _("A new to do item has been added")
        COMPLETED_TODO = "completed_todo", _("To do item has been marked as completed")
        ADDED_RESOURCE = "added_resource", _("A new resource item has been added")
        COMPLETED_COURSE = "completed_course", _("Course has been completed")
        ADDED_BADGE = "added_badge", _("A new badge item has been added")
        ADDED_INTRODUCTION = "added_introduction", _(
            "A new introduction item has been added"
        )
        ADDED_PREBOARDING = "added_preboarding", _(
            "A new preboarding item has been added"
        )
        ADDED_APPOINTMENT = "added_appointment", _(
            "A new appointment item has been added"
        )
        ADDED_NEWHIRE = "added_new_hire", _("A new hire has been added")
        ADDED_ADMIN = "added_administrator", _("A new administrator has been added")
        ADDED_MANAGER = "added_manager", _("A new manager has been added")
        ADDED_ADMIN_TASK = "added_admin_task", _("A new admin task has been added")
        ADDED_SEQUENCE = "added_sequence", _("A new sequence has been added")
        SENT_EMAIL_MESSAGE = "sent_email_message", _("A new email has been sent")
        SENT_TEXT_MESSAGE = "sent_text_message", _("A new text message has been sent")
        SENT_SLACK_MESSAGE = "sent_slack_message", _(
            "A new slack message has been sent"
        )
        UPDATED_SLACK_MESSAGE = "updated_slack_message", _(
            "A new slack message has been updated"
        )
        SENT_EMAIL_LOGIN_CREDENTIALS = "sent_email_login_credentials", _(
            "Login credentials have been sent"
        )
        SENT_EMAIL_TASK_REOPENED = "sent_email_task_reopened", _(
            "Reopened task email has been sent"
        )
        SENT_EMAIL_TASK_REMINDER = "sent_email_task_reminder", _(
            "Task reminder email has been sent"
        )
        SENT_EMAIL_NEWHIRE_CRED = "sent_email_new_hire_credentials", _(
            "Sent new hire credentials email"
        )
        SENT_EMAIL_PREBOARDING_ACCESS = "sent_email_preboarding_access", _(
            "Sent new hire preboarding email"
        )
        SENT_EMAIL_CUSTOM_SEQUENCE = "sent_email_custom_sequence", _(
            "Sent email from sequence"
        )
        SENT_EMAIL_NEWHIRE_UPDATES = "sent_email_new_hire_with_updates", _(
            "Sent email with updates to new hire"
        )
        SENT_EMAIL_ADMIN_TASK_EXTRA = "sent_email_admin_task_extra", _(
            "Sent email to extra person in admin task"
        )
        SENT_EMAIL_ADMIN_TASK_NEW_ASSIGNED = "sent_email_admin_task_new_assigned", _(
            "Sent email about new person assigned to admin task"
        )
        SENT_EMAIL_ADMIN_TASK_NEW_COMMENT = "sent_email_admin_task_new_comment", _(
            "Sent email about new comment on admin task"
        )
        SENT_EMAIL_INTEGRATION_NOTIFICATION = "sent_email_integration_notification", _(
            "Sent email about completing integration call"
        )
        FAILED_NO_PHONE = "failed_no_phone", _(
            "Couldn't send text message: number is missing"
        )
        FAILED_NO_EMAIL = "failed_no_email", _(
            "Couldn't send email message: email is missing"
        )
        FAILED_EMAIL_RECIPIENTS_REFUSED = "failed_email_recipients_refused", _(
            "Couldn't deliver email message: recipient refused"
        )
        FAILED_EMAIL_DELIVERY = "failed_email_delivery", _(
            "Couldn't deliver email message: provider error"
        )
        FAILED_EMAIL_ADDRESS = "failed_email_address", _(
            "Couldn't deliver email message: provider error"
        )
        FAILED_SEND_SLACK_MESSAGE = "failed_send_slack_message", _(
            "Couldn't send Slack message"
        )
        FAILED_UPDATE_SLACK_MESSAGE = "failed_update_slack_message", _(
            "Couldn't update Slack message"
        )
        RAN_INTEGRATION = "ran_integration", _("Integration has been triggered")
        FAILED_INTEGRATION = "failed_integration", _("Couldn't complete integration")
        FAILED_TEXT_INTEGRATION_NOTIFICATION = (
            "failed_text_integration_notification",
            _("Couldn't send integration notification"),
        )

    notification_type = models.CharField(
        choices=Type.choices, max_length=100, default=Type.ADDED_TODO
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

    @property
    def can_delete(self):
        # Only allow delete when it's a sequence item and when it's no more then two
        # days ago when it got added
        return (
            self.notification_type == Notification.Type.ADDED_SEQUENCE
            and self.created > (timezone.now() - timedelta(days=2))
        )
