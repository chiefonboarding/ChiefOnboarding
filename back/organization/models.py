from django.contrib.postgres.fields import ArrayField
from django.db import models
from misc.models import File
from django.conf import settings

LANGUAGES_OPTIONS = (
    ('en', 'English'),
    ('nl', 'Dutch'),
    ('fr', 'French'),
    ('de', 'Deutsch'),
    ('tr', 'Turkish'),
    ('pt', 'Portuguese'),
    ('es', 'Spanish')
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
    new_hire_email = models.BooleanField(default=True)
    new_hire_email_reminders = models.BooleanField(default=True)
    new_hire_email_overdue_reminders = models.BooleanField(default=False)

    # Slack specific
    slack_buttons = models.BooleanField(default=True)
    ask_colleague_welcome_message = models.BooleanField(default=True)
    send_new_hire_start_reminder = models.BooleanField(default=False)
    auto_create_user = models.BooleanField(default=False)
    create_new_hire_without_confirm = models.BooleanField(default=False)
    slack_confirm_person = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    object = ObjectManager()
    objects = models.Manager()


class Tag(models.Model):
    name = models.CharField(max_length=500)


class WelcomeMessage(models.Model):
    MESSAGE_TYPE = (
        (0, 'pre-boarding'),
        (1, 'new hire welcome'),
        (2, 'text welcome'),
        (3, 'slack welcome'),
        (4, 'slack knowledge')
    )

    message = models.CharField(max_length=20250, blank=True)
    language = models.CharField(choices=LANGUAGES_OPTIONS, max_length=3, default='en')
    message_type = models.IntegerField(choices=MESSAGE_TYPE, default=0)


class TemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(template=True)

class FullManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('content__files')

class FullTemplateManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related('content__files').filter(template=True)


class BaseTemplate(models.Model):
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
                if i != '':
                    Tag.objects.get_or_create(name=i)
        super(BaseTemplate, self).save(*args, **kwargs)
