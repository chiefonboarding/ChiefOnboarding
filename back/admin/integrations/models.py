import base64
import json
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django_q.models import Schedule
from django_q.tasks import schedule
from fernet_fields import EncryptedTextField
from requests.exceptions import (
    HTTPError,
    InvalidHeader,
    InvalidJSONError,
    InvalidSchema,
    InvalidURL,
    JSONDecodeError,
    MissingSchema,
    SSLError,
    Timeout,
    TooManyRedirects,
    URLRequired,
)
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

    def run_request(self, data):
        url = self._replace_vars(data["url"])
        if "data" in data:
            post_data = self._replace_vars(json.dumps(data["data"]))
        else:
            post_data = {}
        if data.get("cast_data_to_json", False):
            try:
                post_data = json.loads(post_data)
            except Exception:
                pass
        try:
            response = requests.request(
                data.get("method", "POST"),
                url,
                headers=self.headers(data.get("headers", {})),
                data=post_data,
                timeout=120,
            )
        except (InvalidJSONError, JSONDecodeError):
            return False, "JSON is invalid"

        except HTTPError:
            return False, "An HTTP error occurred"

        except SSLError:
            return False, "An SSL error occurred"

        except Timeout:
            return False, "The request timed out"

        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL):
            return False, "The url is invalid"

        except TooManyRedirects:
            return False, "There are too many redirects"

        except InvalidHeader:
            return False, "The header is invalid"

        except:  # noqa E722
            return False, "There was an unexpected error with the request"

        if data.get("fail_when_4xx_response_code", True):
            try:
                response.raise_for_status()
            except Exception:
                return False, response.text

        return True, response

    def _replace_vars(self, text):
        params = {} if not hasattr(self, "params") else self.params
        params["redirect_url"] = settings.BASE_URL + reverse_lazy(
            "integrations:oauth-callback", args=[self.id]
        )
        if hasattr(self, "new_hire") and self.new_hire is not None:
            text = self.new_hire.personalize(text, self.extra_args | params)
            return text
        t = Template(text)
        context = Context(self.extra_args | params)
        text = t.render(context)
        return text

    @property
    def has_oauth(self):
        return "oauth" in self.manifest

    def headers(self, headers={}):
        headers = (
            self.manifest.get("headers", {}).items()
            if len(headers) == 0
            else headers.items()
        )
        new_headers = {}
        for key, value in headers:
            # If Basic authentication then swap to base64
            if key == "Authorization" and value.startswith("Basic"):
                auth_details = self._replace_vars(value.split(" ", 1)[1])
                value = "Basic " + base64.b64encode(
                    auth_details.encode("ascii")
                ).decode("ascii")

            # Adding an empty string to force to return a string instead of a
            # safestring. Ref: https://github.com/psf/requests/issues/6159
            new_headers[self._replace_vars(key) + ""] = self._replace_vars(value) + ""
        return new_headers

    def user_exists(self, new_hire):
        self.new_hire = new_hire

        # Renew token if necessary
        if not self.renew_key():
            return

        success, response = self.run_request(self.manifest["exists"])

        if not success:
            return None

        return self._replace_vars(self.manifest["exists"]["expected"]) in response.text

    def renew_key(self):
        # Oauth2 refreshing access token if needed
        success = True
        if (
            self.has_oauth
            and "expires_in" in self.extra_args.get("oauth", {})
            and self.expiring < timezone.now()
        ):
            success, response = self.run_request(self.manifest["oauth"]["refresh"])

            if not success:
                Notification.objects.create(
                    notification_type="failed_integration",
                    extra_text=self.name,
                    created_for=self.new_hire,
                    description="Refresh url: " + str(response),
                )
                return success

            self.extra_args["oauth"] |= response.json()
            if "expires_in" in response.json():
                self.expiring = timezone.now() + timedelta(
                    seconds=response.json()["expires_in"]
                )
            self.save()
        return success

    def execute(self, new_hire, params):
        self.params = params
        self.params |= new_hire.extra_fields
        self.new_hire = new_hire

        # Renew token if necessary
        if not self.renew_key():
            return False

        # Add generated secrets
        for item in self.manifest["initial_data_form"]:
            if "name" in item and item["name"] == "generate":
                self.extra_args[item["id"]] = get_random_string(length=10)

        # Run all requests
        for item in self.manifest["execute"]:
            success, response = self.run_request(item)

            if not success:
                Notification.objects.create(
                    notification_type="failed_integration",
                    extra_text=self.name,
                    created_for=new_hire,
                    description=f"Execute url ({item['url']}): {response}",
                )
                # Retry url in one hour
                try:
                    schedule(
                        "admin.integrations.tasks.retry_integration",
                        new_hire.id,
                        self.id,
                        params,
                        name=(
                            f"Retrying integration {self.id} for new hire {new_hire.id}"
                        ),
                        next_run=timezone.now() + timedelta(hours=1),
                        schedule_type=Schedule.ONCE,
                    )
                except:  # noqa E722
                    # Only errors when item gets added another time, so we can safely
                    # let it pass.
                    pass
                # return False

        # Run all post requests (notifications)
        for item in self.manifest.get("post_execute_notification", []):
            if item["type"] == "email":
                send_email_with_notification(
                    subject=self._replace_vars(item["subject"]),
                    message=self._replace_vars(item["message"]),
                    to=self._replace_vars(item["to"]),
                    notification_type="sent_email_integration_notification",
                )
                return True
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
                except Exception:
                    Notification.objects.create(
                        notification_type="failed_text_integration_notification",
                        extra_text=self.name,
                        created_for=new_hire,
                    )
                    return True

        # Succesfully ran integration, add notification
        Notification.objects.create(
            notification_type="ran_integration",
            extra_text=self.name,
            created_for=new_hire,
        )
        return True

    def config_form(self, data=None):
        from .forms import IntegrationConfigForm

        return IntegrationConfigForm(instance=self, data=data)

    objects = IntegrationManager()
