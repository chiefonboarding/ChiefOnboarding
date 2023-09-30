import time
import base64
import io
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

from admin.integrations.utils import get_value_from_notation
from misc.fernet_fields import EncryptedTextField
from misc.fields import EncryptedJSONField
from organization.models import Notification
from organization.utils import send_email_with_notification


class IntegrationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def sequence_integration_options(self):
        # any webhooks and account provisioning
        return self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type=Integration.ManifestType.WEBHOOK,
        )

    def account_provision_options(self):
        # only account provisioning (no general webhooks)
        return self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type=Integration.ManifestType.WEBHOOK,
            manifest__exists__isnull=False,
        )

    def import_users_options(self):
        # only import user items
        return self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type=Integration.ManifestType.USER_IMPORT,
        )


class Integration(models.Model):
    class Type(models.IntegerChoices):
        SLACK_BOT = 0, _("Slack bot")
        SLACK_ACCOUNT_CREATION = 1, _("Slack account creation")  # legacy
        GOOGLE_ACCOUNT_CREATION = 2, _("Google account creation")  # legacy
        GOOGLE_LOGIN = 3, _("Google Login")
        ASANA = 4, _("Asana")  # legacy
        CUSTOM = 10, _("Custom")

    class ManifestType(models.IntegerChoices):
        WEBHOOK = 0, _("Provision user accounts or trigger webhooks")
        USER_IMPORT = 1, _("Import users")

    name = models.CharField(max_length=300, default="", blank=True)
    integration = models.IntegerField(choices=Type.choices)
    manifest_type = models.IntegerField(
        choices=ManifestType.choices, null=True, blank=True
    )
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

    @property
    def has_user_context(self):
        return self.manifest_type == Integration.ManifestType.WEBHOOK

    def run_request(self, data, file=None):
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
                files={data.get("send_file_as"): file.getvalue()}
                if data.get("send_file_as", False) and file is not None
                else None,
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

        except Exception as e:  # noqa E722
            print(e)

            return False, "There was an unexpected error with the request"

        if data.get("fail_when_4xx_response_code", True):
            print(response.status_code)
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

    def headers(self, headers=None):
        if headers is None:
            headers = {}

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
                user = self.new_hire if self.has_user_context else None
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_INTEGRATION,
                    extra_text=self.name,
                    created_for=user,
                    description="Refresh url: " + str(response),
                )
                return success

            self.extra_args["oauth"] |= response.json()
            if "expires_in" in response.json():
                self.expiring = timezone.now() + timedelta(
                    seconds=response.json()["expires_in"]
                )
            self.save(update_fields=["expiring", "extra_args"])
        return success

    def _check_condition(self, response, condition):
        value = self._replace_vars(condition.get("value"))
        try:
            # first argument will be taken from the response
            response_value = get_value_from_notation(
                condition.get("response_notation"), response.json()
            )
        except KeyError:
            # we know that the result might not be in the response yet, as we are
            # waiting for the correct response, so just respond with an empty string
            response_value = ""
        return value == response_value

    def _polling(self, item, response):
        polling = item.get("polling")
        continue_if = item.get("continue_if")
        interval = polling.get("interval")
        amount = polling.get("amount")

        got_expected_result = self._check_condition(response, continue_if)
        if got_expected_result:
            return True, response

        tried = 1
        while amount > tried:
            time.sleep(interval)
            success, response = self.run_request(item)
            got_expected_result = self._check_condition(response, continue_if)
            if got_expected_result:
                return True, response
            tried += 1
        # if exceeding the max amounts, then fail
        return False, response

    def execute(self, new_hire, params):
        # Only one file can be used per integration
        file = None

        self.params = params
        self.params["responses"] = []
        if self.has_user_context:
            self.params |= new_hire.extra_fields
            self.new_hire = new_hire

        # Renew token if necessary
        if not self.renew_key():
            return False, None

        # Add generated secrets
        for item in self.manifest.get("initial_data_form", []):
            if "name" in item and item["name"] == "generate":
                self.extra_args[item["id"]] = get_random_string(length=10)

        # Run all requests
        for item in self.manifest["execute"]:
            success, response = self.run_request(item, file=file)

            # check if we need to poll before continuing
            if polling := item.get("polling", False):
                success, response = self._polling(item, response)

            # check if we need to block this integration based on condition
            if continue_if := item.get("continue_if", False):
                got_expected_result = self._check_condition(response, continue_if)
                if not got_expected_result:
                    response = self.clean_response(response=response)
                    Notification.objects.create(
                        notification_type=Notification.Type.BLOCKED_INTEGRATION,
                        extra_text=self.name,
                        created_for=new_hire,
                        description=f"Execute url ({item['url']}): {response}",
                    )
                    return False, response

            # No need to retry or log when we are importing users
            if not success and self.has_user_context:
                response = self.clean_response(response=response)
                if polling:
                    response = "Polling timed out: " + response
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_INTEGRATION,
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
                return False, response

            # save if file, so we can reuse later
            return_type = item.get("type", "JSON")
            if return_type == "file":
                file = io.BytesIO(response.content)

            # save json response temporarily to be reused in other parts
            if return_type == "JSON":
                self.params["responses"].append(response)
            else:
                self.params["responses"].append({})

            # store data coming back from response to the user, so we can reuse in other
            # integrations
            if store_data := item.get("store_data", {}):
                for new_hire_prop, notation_for_response in store_data.items():
                    try:
                        value = get_value_from_notation(
                            notation_for_response, response.json()
                        )
                    except KeyError:
                        return (
                            False,
                            f"Could not store data to new hire: {notation_for_response}"
                            f" not found in {self.clean_response(response.json())}",
                        )

                    # save to new hire and to temp var `params` on this model for use in
                    # the same integration
                    new_hire.extra_fields[new_hire_prop] = value
                    self.params[new_hire_prop] = value
                new_hire.save()

        # Run all post requests (notifications)
        for item in self.manifest.get("post_execute_notification", []):
            if item["type"] == "email":
                send_email_with_notification(
                    subject=self._replace_vars(item["subject"]),
                    message=self._replace_vars(item["message"]),
                    to=self._replace_vars(item["to"]),
                    notification_type=(
                        Notification.Type.SENT_EMAIL_INTEGRATION_NOTIFICATION
                    ),
                )
                return True, None
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
                        notification_type=(
                            Notification.Type.FAILED_TEXT_INTEGRATION_NOTIFICATION
                        ),
                        extra_text=self.name,
                        created_for=new_hire,
                    )
                    return True, None

        # Succesfully ran integration, add notification only when we are provisioning
        # access
        if self.has_user_context:
            Notification.objects.create(
                notification_type=Notification.Type.RAN_INTEGRATION,
                extra_text=self.name,
                created_for=new_hire,
            )
        return True, response

    def config_form(self, data=None):
        from .forms import IntegrationConfigForm

        return IntegrationConfigForm(instance=self, data=data)

    def clean_response(self, response):
        # if json, then convert to string to make it easier to replace values
        response = str(response)
        for name, value in self.extra_args.items():
            response = response.replace(
                str(value), _("***Secret value for %(name)s***") % {"name": name}
            )

        return response

    objects = IntegrationManager()
