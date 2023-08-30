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

from admin.integrations.exceptions import GettingUsersError, KeyIsNotInDataError
from admin.integrations.utils import get_value_from_notation
from misc.fernet_fields import EncryptedTextField
from misc.fields import EncryptedJSONField
from organization.models import Notification
from organization.utils import send_email_with_notification


class IntegrationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def sequence_integration_options(self):
        return self.get_queryset().filter(integration=Integration.Type.CUSTOM)

    def account_provision_options(self):
        return (
            self.get_queryset()
            .filter(integration=Integration.Type.CUSTOM, manifest__exists__isnull=False)
            .exclude(manifest__type="import_users")
        )

    def import_users_options(self):
        return self.get_queryset().filter(integration=10, manifest__type="import_users")


class Integration(models.Model):
    class Type(models.IntegerChoices):
        SLACK_BOT = 0, _("Slack bot")
        SLACK_ACCOUNT_CREATION = 1, _("Slack account creation")  # legacy
        GOOGLE_ACCOUNT_CREATION = 2, _("Google account creation")  # legacy
        GOOGLE_LOGIN = 3, _("Google Login")
        ASANA = 4, _("Asana")  # legacy
        CUSTOM = 10, _("Custom")

    name = models.CharField(max_length=300, default="", blank=True)
    integration = models.IntegerField(choices=Type.choices)
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

    @property
    def is_import_user_action(self):
        return "import_user" in self.manifest

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
                    notification_type=Notification.Type.FAILED_INTEGRATION,
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
        if not self.is_import_user_action:
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

            # No need to retry or log when we are importing users
            if not success and not self.is_import_user_action:
                response = self.clean_response(response=response)
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
        if not self.is_import_user_action:
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
            response = response.replace(str(value), f"***Secret value for {name}***")

        return response

    def extract_users_from_list_response(self, response):
        # Building list of users from response. Dig into response to get to the users.
        data_from = self.manifest["data_from"]
        users = get_value_from_notation(data_from, response.json())

        data_structure = self.manifest["data_structure"]
        user_details = []
        for user_data in users:
            user = {}
            for prop, notation in data_structure.items():
                try:
                    user[prop] = get_value_from_notation(notation, user_data)
                except KeyError:
                    # This is unlikely to go wrong - only when api changes or when
                    # configs are being setup
                    raise KeyIsNotInDataError(
                        f"Notation '{notation}' not in {self.clean_response(user_data)}"
                    )
            user_details.append(user)
        return user_details

    def get_next_page(self, response):
        # Some apis give us back a full URL, others just a token. If we get a full URL,
        # follow that, if we get a token, then also specify the next_page. The token
        # gets placed through the NEXT_PAGE_TOKEN variable.

        # taken from response - full url including params for next page
        next_page_from = self.manifest.get("next_page_from")

        # build up url ourself based on hardcoded url + token for next part
        next_page_token_from = self.manifest.get("next_page_token_from")
        # hardcoded in manifest
        next_page = self.manifest.get("next_page")

        # skip if none provided
        if not next_page_from and not (next_page_token_from and next_page):
            return

        if next_page_from:
            try:
                return get_value_from_notation(next_page_from, response)
            except KeyError:
                # next page was not provided anymore, so we are done
                return

        # Build next url from next_page and next_page_token_from
        try:
            token = get_value_from_notation(next_page_token_from, response)
        except KeyError:
            # next page token was not provided anymore, so we are done
            return

        # Replace token variable with real token
        self.params["NEXT_PAGE_TOKEN"] = token
        return self._replace_vars(next_page)

    def get_import_user_candidates(self, user):
        success, response = self.execute(user, {})
        if not success:
            raise GettingUsersError(self.clean_response(response))

        # It's fine if this fails, the exception is caught in function that calls this
        # function
        users = self.extract_users_from_list_response(response)

        # If we don't care about next pages, then just return the users
        if self.get_next_page(response) is None:
            return users

        amount_pages_to_fetch = self.manifest.get("amount_pages_to_fetch", 5)
        fetched_pages = 1
        while amount_pages_to_fetch != fetched_pages:
            # End everything if next page does not exist
            if next_page_url := self.get_next_page(response) is None:
                break

            success, response = self.run_request(
                {"method": "GET", "url": next_page_url}
            )
            if not success:
                raise GettingUsersError(
                    "Paginated URL fetch: " + self.clean_response(response)
                )

            users += self.extract_users_from_list_response(response)
            fetched_pages += 1

        return users

    objects = IntegrationManager()
