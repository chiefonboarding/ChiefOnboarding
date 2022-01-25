import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from fernet_fields import EncryptedTextField

INTEGRATION_OPTIONS = (
    (0, "Slack bot"),
    (1, "Slack account creation"),
    (2, "Google account creation"),
    (3, "Google Login"),
    (4, "Asana"),
)
INTEGRATION_OPTIONS_URLS = [
    (reverse_lazy("settings:slack-bot"), reverse_lazy("settings:google-login")),
    (reverse_lazy("settings:slack-account"), reverse_lazy("settings:google-login")),
    (reverse_lazy("settings:google-account"), reverse_lazy("settings:google-account")),
    (reverse_lazy("settings:google-login"), reverse_lazy("settings:google-login")),
    (reverse_lazy("settings:asana"), reverse_lazy("settings:asana")),
]
STATUS = ((0, "pending"), (1, "completed"), (2, "waiting on user"))


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
    one_time_auth_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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


class ScheduledAccess(models.Model):
    new_hire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    integration = models.IntegerField(choices=INTEGRATION_OPTIONS)
    status = models.IntegerField(choices=STATUS, default=0)
    email = models.EmailField(max_length=22300, null=True, blank=True)
