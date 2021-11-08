from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from misc.models import File

LANGUAGES_OPTIONS = (
    ("en", "English"),
    ("nl", "Dutch"),
    ("fr", "French"),
    ("de", "German"),
    ("tr", "Turkish"),
    ("pt", "Portuguese"),
    ("es", "Spanish"),
)


class ObjectManager(models.Manager):
    def get(self):
        return self.get_queryset()[0]


class Organization(models.Model):
    name = models.CharField(max_length=500)
    language = models.CharField(default="en", max_length=10, choices=LANGUAGES_OPTIONS)
    timezone = models.CharField(default="UTC", max_length=1000)

    # customization
    base_color = models.CharField(max_length=10, default="#99835C")
    accent_color = models.CharField(max_length=10, default="#ffbb42")
    bot_color = models.CharField(max_length=10, default="#ffbb42")
    logo = models.ForeignKey(File, on_delete=models.CASCADE, null=True)

    # login options
    credentials_login = models.BooleanField(default=True)
    google_login = models.BooleanField(default=False)
    slack_login = models.BooleanField(default=False)

    # additional settings
    new_hire_email = models.BooleanField(
        verbose_name="Send email to new hire with login credentials",
        help_text="This is essential if you want your new hires to login to the dashboard (disable if using Slack)",
        default=True,
    )
    new_hire_email_reminders = models.BooleanField(
        verbose_name="Send email to new hire with updates",
        help_text="Think of new tasks that got assigned, new resources, badges... ",
        default=True,
    )
    new_hire_email_overdue_reminders = models.BooleanField(
        verbose_name="Send email to new hire when tasks are overdue",
        help_text="These are daily emails, until all overdue tasks are completed.",
        default=False,
    )

    # Slack specific
    slack_buttons = models.BooleanField(
        verbose_name="Add 'todo' and 'resource' buttons to the first message that's being sent to the new hire.",
        help_text="Slack only",
        default=True,
    )
    ask_colleague_welcome_message = models.BooleanField(
        verbose_name="Send a Slack message to the team to collect personal welcome messages from colleages.",
        help_text="Slack only",
        default=True,
    )
    send_new_hire_start_reminder = models.BooleanField(
        verbose_name="Send a Slack message to the team on the day the new hire starts",
        help_text="Slack only",
        default=False,
    )
    auto_create_user = models.BooleanField(
        verbose_name="Create a new hire when they join your Slack team",
        help_text="If the user does not exist yet - Slack only",
        default=False,
    )
    create_new_hire_without_confirm = models.BooleanField(
        verbose_name="Create new hires without needing confirm from a user",
        help_text="Slack only",
        default=False,
    )
    slack_confirm_person = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    object = ObjectManager()
    objects = models.Manager()


class Tag(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class WelcomeMessage(models.Model):
    MESSAGE_TYPE = (
        (0, "pre-boarding"),
        (1, "new hire welcome"),
        (2, "text welcome"),
        (3, "slack welcome"),
        (4, "slack knowledge"),
    )

    message = models.CharField(max_length=20250, blank=True)
    language = models.CharField(choices=LANGUAGES_OPTIONS, max_length=3, default="en")
    message_type = models.IntegerField(choices=MESSAGE_TYPE, default=0)


class TemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(template=True)


class FullManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("content__files")


class FullTemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("content__files").filter(template=True)


class BaseItem(models.Model):
    name = models.CharField(max_length=240)
    tags = ArrayField(models.CharField(max_length=10200), blank=True)
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


class Changelog(models.Model):
    added = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField(default="")

    class Meta:
        ordering = ["-id"]
