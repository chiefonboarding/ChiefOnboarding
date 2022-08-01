import json
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task
from fernet_fields import EncryptedTextField
from twilio.rest import Client

from misc.fields import EncryptedJSONField
from organization.models import Notification
from organization.utils import send_email_with_notification

INTEGRATION_OPTIONS = (
    (0, _("Slack bot")),
    (1, _("Slack account creation")),
    (2, _("Google account creation")),
    (3, _("Google Login")),
    (4, _("Asana")),
)


class IntegrationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def sequence_integration_options(self):
        return self.get_queryset().filter(integration=10)

    def account_provision_options(self):
        return self.get_queryset().filter(
            integration=10, manifest__exists__isnull=False
        )


class Integration(models.Model):
    name = models.CharField(max_length=300, default="", blank=True)
    integration = models.IntegerField(choices=INTEGRATION_OPTIONS)
    token = EncryptedTextField(max_length=10000, default="", blank=True)
    refresh_token = EncryptedTextField(max_length=10000, default="", blank=True)
    base_url = models.CharField(max_length=22300, default="", blank=True)
    redirect_url = models.CharField(max_length=22300, default="", blank=True)
    account_id = models.CharField(max_length=22300, default="", blank=True)
    active = models.BooleanField(default=True)
    ttl = models.IntegerField(null=True, blank=True)
    expiring = models.DateTimeField(auto_now_add=True, blank=True)
    one_time_auth_code = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )

    manifest = models.JSONField(default=dict)
    extra_args = EncryptedJSONField(default=dict)
    enabled_oauth = models.BooleanField(default=False)

    # Slack
    app_id = models.CharField(max_length=100, default="")
    client_id = models.CharField(max_length=100, default="")
    client_secret = models.CharField(max_length=100, default="")
    signing_secret = models.CharField(max_length=100, default="")
    verification_token = models.CharField(max_length=100, default="")
    bot_token = EncryptedTextField(max_length=10000, default="", blank=True)
    bot_id = models.CharField(max_length=100, default="")

    def _run_request(self, data):
        url = self._replace_vars(data["url"])
        if "data" in data:
            post_data = json.loads(self._replace_vars(json.dumps(data["data"])))
        else:
            post_data = {}
        return requests.request(
            data.get("method", "POST"),
            url,
            headers=self._headers,
            data=post_data,
            timeout=120,
        ).json()

    def _replace_vars(self, text):
        params = {} if not hasattr(self, "params") else self.params
        if hasattr(self, "new_hire") and self.new_hire is not None:
            text = self.new_hire.personalize(text, self.extra_args)
        t = Template(text)
        context = Context(self.extra_args | params)
        text = t.render(context)
        return text

    @property
    def has_oauth(self):
        return "oauth" in self.manifest

    @property
    def _headers(self):
        new_headers = {}
        for key, value in self.manifest["headers"].items():
            new_headers[self._replace_vars(key)] = self._replace_vars(value)
        return new_headers

    def user_exists(self, new_hire):
        self.new_hire = new_hire
        return self._replace_vars(self.manifest["exists"]["expected"]) in json.dumps(
            self._run_request(self.manifest["exists"])
        )

    def execute(self, new_hire, params):
        self.params = params
        self.new_hire = new_hire

        # Renew access key if necessary
        if (
            self.has_oauth
            and "expires_in" in self.extra_args
            and self.expiring < timezone.now()
        ):
            try:
                self.extra_args |= self._run_request(
                    self.manifest["oauth"]["refresh_url"]
                ).json()
            except requests.RequestException as e:
                Notification.objects.create(
                    notification_type="failed_integration",
                    extra_text=self.name,
                    created_for=new_hire,
                    description=str(e),
                )
            self.save()

        # Add generated secrets
        for item in self.manifest["initial_data_form"]:
            if "type" in item and item["type"] == "generate":
                self.extra_args[item["id"]] = get_random_string(length=10)

        # Run all requests
        for item in self.manifest["execute"]:
            try:
                self._run_request(item)
            except requests.RequestException as e:
                Notification.objects.create(
                    notification_type="failed_integration",
                    extra_text=self.name,
                    created_for=new_hire,
                    description=str(e),
                )
                # Retry url in one hour
                async_task(
                    "admin.integrations.tasks.retry_integration",
                    new_hire.id,
                    self.id,
                    params,
                    task_name=f"Retrying integration {self.name}",
                    next_run=timezone.now() + timedelta(hours=1),
                )
                return

        # Run all post requests (notifications)
        for item in self.manifest.get("post_execute_notification", []):
            if item["type"] == "email":
                send_email_with_notification(
                    subject=self._replace_vars(item["subject"]),
                    message=self._replace_vars(item["message"]),
                    to=self._replace_vars(item["to"]),
                    notification_type="sent_email_integration_notification",
                )
            else:
                try:
                    client = Client(
                        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                    )
                    client.messages.create(
                        to=new_hire.phone,
                        from_=settings.TWILIO_FROM_NUMBER,
                        body=self._replace_vars(item["message"]),
                    )
                except Exception as e:
                    Notification.objects.create(
                        notification_type="failed_text_integration_notification",
                        extra_text=self.name,
                        created_for=new_hire,
                        description=str(e),
                    )

        # Succesfully ran integration, add notification
        Notification.objects.create(
            notification_type="ran_integration",
            extra_text=self.name,
            created_for=new_hire,
        )

    def config_form(self, data=None):
        from .forms import IntegrationConfigForm

        return IntegrationConfigForm(instance=self, data=data)

    objects = IntegrationManager()
