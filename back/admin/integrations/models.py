import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from fernet_fields import EncryptedTextField

INTEGRATION_OPTIONS = (
    (0, _("Slack bot")),
    (1, _("Slack account creation")),
    (2, _("Google account creation")),
    (3, _("Google Login")),
    (4, _("Asana")),
)
INTEGRATION_OPTIONS_URLS = [
    {
        "create_url": reverse_lazy("settings:slack-bot"),
        "disabled": False,
        "disable_url": reverse_lazy("settings:google-login"),
        "extra_action_url": "settings:slack-account-update-channels",
        "extra_action_text": _("Update Slack channels list"),
    },
    {
        "disabled": True,
        "create_url": reverse_lazy("settings:slack-account"),
        "disable_url": reverse_lazy("settings:google-login"),
    },
    {
        "disabled": False,
        "create_url": reverse_lazy("settings:google-account"),
        "disable_url": reverse_lazy("settings:google-account"),
    },
    {
        "disabled": False,
        "create_url": reverse_lazy("settings:google-login"),
        "disable_url": reverse_lazy("settings:google-account"),
    },
    {
        "disabled": False,
        "create_url": reverse_lazy("settings:asana"),
        "disable_url": reverse_lazy("settings:asana"),
    },
]


class AccessTokenManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def account_provision_options(self):
        # Add items here that are meant for account creation. Making it static, as this won't change.
        return self.get_queryset().filter(integration__in=[1, 2, 4])


class AccessToken(models.Model):
    integration = models.IntegerField(choices=INTEGRATION_OPTIONS)
    token = EncryptedTextField(max_length=10000, default="", blank=True)
    refresh_token = EncryptedTextField(max_length=10000, default="", blank=True)
    base_url = models.CharField(max_length=22300, default="", blank=True)
    redirect_url = models.CharField(max_length=22300, default="", blank=True)
    account_id = models.CharField(max_length=22300, default="", blank=True)
    active = models.BooleanField(default=True)
    ttl = models.IntegerField(null=True, blank=True)
    expiring = models.DateTimeField(null=True, blank=True)
    one_time_auth_code = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )

    # Slack
    app_id = models.CharField(max_length=100, default="")
    client_id = models.CharField(max_length=100, default="")
    client_secret = models.CharField(max_length=100, default="")
    signing_secret = models.CharField(max_length=100, default="")
    verification_token = models.CharField(max_length=100, default="")
    bot_token = EncryptedTextField(max_length=10000, default="", blank=True)
    bot_id = models.CharField(max_length=100, default="")

    @property
    def name(self):
        return self.get_integration_display()

    @property
    def account_provision_name(self):
        # Used with sequences
        if self.integration == 1:
            return 'slack'
        if self.integration == 3:
            return 'google'
        if self.integration == 4:
            return 'asana'


    def api_class(self):
        from .asana import Asana
        from .google import Google
        from .slack import Slack

        if self.integration == 1:
            return Slack()
        if self.integration == 3:
            return Google()
        if self.integration == 4:
            return Asana()

    def add_user_form_class(self):
        from .forms import AddAsanaUserForm, AddGoogleUserForm, AddSlackUserForm

        if self.integration == 1:
            return AddSlackUserForm()
        if self.integration == 3:
            return AddGoogleUserForm()
        if self.integration == 4:
            return AddAsanaUserForm

    def add_user(self, user, params):
        self.api_class().add_user(user, params)

    objects = AccessTokenManager()


