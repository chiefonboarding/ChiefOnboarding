import base64
import io
import json
import time
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
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

from admin.integrations.serializers import (
    SyncUsersManifestSerializer,
    WebhookManifestSerializer,
)
from admin.integrations.utils import get_value_from_notation
from misc.fernet_fields import EncryptedTextField
from misc.fields import EncryptedJSONField
from organization.models import Notification
from organization.utils import has_manager_or_buddy_tags, send_email_with_notification


class IntegrationTracker(models.Model):
    """Model to track the integrations that ran. Gives insights into error messages"""
    class Category(models.IntegerChoices):
        EXECUTE = 0, _("Run the execute part")
        EXISTS = 1, _("Check if user exists")
        REVOKE = 2, _("Revoke user")

    integration = models.ForeignKey("integrations.Integration", on_delete=models.CASCADE)
    category = models.IntegerField(choices=Category.choices)
    for_user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    ran_at = models.DateTimeField(auto_now_add=True)

    @property
    def ran_execute_block(self):
        return self.category == IntegrationTracker.Category.EXECUTE

    @property
    def ran_exists_block(self):
        return self.category == IntegrationTracker.Category.EXISTS

    @property
    def ran_revoke_block(self):
        return self.category == IntegrationTracker.Category.REVOKE


class IntegrationTrackerStep(models.Model):
    tracker = models.ForeignKey("integrations.IntegrationTracker", on_delete=models.CASCADE, related_name="steps")
    status_code = models.IntegerField()
    json_response = models.JSONField()
    text_response = models.TextField()
    url = models.TextField()
    method = models.TextField()
    post_data = models.JSONField()
    headers = models.JSONField()
    error = models.TextField()

    @property
    def has_succeeded(self):
        return self.status_code >= 200 and self.status_code < 300

    @property
    def pretty_json_response(self):
        return json.dumps(self.json_response, indent=4)

    @property
    def pretty_headers(self):
        return json.dumps(self.headers, indent=4)

    @property
    def pretty_post_data(self):
        return json.dumps(self.post_data, indent=4)



class IntegrationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def sequence_integration_options(self):
        # any webhooks and account provisioning
        return self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type__in=[
                Integration.ManifestType.WEBHOOK,
                Integration.ManifestType.MANUAL_USER_PROVISIONING,
            ],
        )

    def account_provision_options(self):
        # only account provisioning (no general webhooks)
        return self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type=Integration.ManifestType.WEBHOOK,
            manifest__exists__isnull=False,
        ) | self.get_queryset().filter(
            integration=Integration.Type.CUSTOM,
            manifest_type=Integration.ManifestType.MANUAL_USER_PROVISIONING,
        )

    def import_users_options(self):
        # only import user items
        return (
            self.get_queryset()
            .filter(
                integration=Integration.Type.CUSTOM,
                manifest_type=Integration.ManifestType.SYNC_USERS,
            )
            .exclude(manifest__schedule__isnull=False)
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
        SYNC_USERS = 1, _("Sync users")
        MANUAL_USER_PROVISIONING = 3, _(
            "Manual user account provisioning, no manifest required"
        )

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

    manifest = models.JSONField(default=dict, null=True, blank=True)
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
    def skip_user_provisioning(self):
        return self.manifest_type == Integration.ManifestType.MANUAL_USER_PROVISIONING

    @property
    def can_revoke_access(self):
        return self.manifest.get("revoke", False)

    @property
    def update_url(self):
        return reverse("integrations:update", args=[self.id])

    def get_icon_template(self):
        return render_to_string("_integration_config.html")

    @property
    def schedule_name(self):
        return f"User sync for integration: {self.id}"

    @property
    def requires_assigned_manager_or_buddy(self):
        # returns manager, buddy
        return has_manager_or_buddy_tags(self.manifest)

    def clean(self):
        if not self.manifest or self.skip_user_provisioning:
            # ignore field if form doesn't have it or no manifest is necessary
            return

        if self.manifest_type == Integration.ManifestType.WEBHOOK:
            manifest_serializer = WebhookManifestSerializer(data=self.manifest)
        else:
            manifest_serializer = SyncUsersManifestSerializer(data=self.manifest)
        if not manifest_serializer.is_valid():
            raise ValidationError({"manifest": json.dumps(manifest_serializer.errors)})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # skip if it's not a sync user integration (no background jobs for the others)
        if self.manifest_type != Integration.ManifestType.SYNC_USERS:
            return

        # update the background job based on the manifest
        schedule_cron = self.manifest.get("schedule")

        try:
            schedule_obj = Schedule.objects.get(name=self.schedule_name)
        except Schedule.DoesNotExist:
            # Schedule does not exist yet, so create it if specified
            if schedule_cron:
                schedule(
                    "admin.integrations.tasks.sync_user_info",
                    self.id,
                    schedule_type=Schedule.CRON,
                    cron=schedule_cron,
                    name=self.schedule_name,
                )
            return

        # delete if cron was removed
        if schedule_cron is None:
            schedule_obj.delete()
            return

        # if schedule changed, then update
        if schedule_obj.cron != schedule_cron:
            schedule_obj.cron = schedule_cron
            schedule_obj.save()

    def register_manual_integration_run(self, user):
        from users.models import IntegrationUser

        integration_user, created = IntegrationUser.objects.update_or_create(
            user=user,
            integration=self,
            defaults={"revoked": user.is_offboarding},
        )

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

        # extract files from locally saved files and send them with the request
        files_to_send = {}
        for field_name, file_name in data.get("files", {}).items():
            try:
                files_to_send[field_name] = (file_name, self.params["files"][file_name])
            except KeyError:
                return (
                    False,
                    f"{file_name} could not be found in the locally saved files",
                )

        error = ""

        try:
            response = requests.request(
                data.get("method", "POST"),
                url,
                headers=self.headers(data.get("headers", {})),
                data=post_data,
                files=files_to_send,
                timeout=120,
            )
        except (InvalidJSONError, JSONDecodeError):
            error = "JSON is invalid"

        except HTTPError:
            error = "An HTTP error occurred"

        except SSLError:
            error = "An SSL error occurred"

        except Timeout:
            error = "The request timed out"

        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL):
            error = "The url is invalid"

        except TooManyRedirects:
            error = "There are too many redirects"

        except InvalidHeader:
            error = "The header is invalid"

        except:  # noqa E722
            error = "There was an unexpected error with the request"

        if error == "" and data.get("fail_when_4xx_response_code", True):
            try:
                response.raise_for_status()
            except Exception:
                error = response.text

        try:
            json_response = response.json()
            text_response = ""
        except:
            json_response = {}
            text_response = response.text


        if hasattr(self, "tracker"):
            IntegrationTrackerStep.objects.create(
                tracker=self.tracker,
                status_code=response.status_code,
                json_response=json.loads(self.clean_response(json_response)),
                text_response=self.clean_response(text_response),
                url=self.clean_response(url),
                method=data.get("method", "POST"),
                post_data=json.loads(self.clean_response(post_data)),
                headers=json.loads(self.clean_response(self.headers(data.get("headers", {})))),
                error=error
            )

        if error != "":
            return False, error

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
        from users.models import IntegrationUser

        # check if user has been created manually
        if self.skip_user_provisioning:
            try:
                user_integration = IntegrationUser.objects.get(
                    user=new_hire, integration=self
                )
            except IntegrationUser.DoesNotExist:
                return False

            return not user_integration.revoked

        self.tracker = IntegrationTracker.objects.create(category=IntegrationTracker.Category.EXISTS, integration=self, for_user=new_hire)

        self.new_hire = new_hire
        self.has_user_context = new_hire is not None

        # Renew token if necessary
        if not self.renew_key():
            return

        success, response = self.run_request(self.manifest["exists"])

        if not success:
            return None

        user_exists = (
            self._replace_vars(self.manifest["exists"]["expected"]) in response.text
        )

        IntegrationUser.objects.update_or_create(
            integration=self, user=new_hire, defaults={"revoked": not user_exists}
        )

        return user_exists

    def needs_user_info(self, user):
        if self.skip_user_provisioning:
            return False

        # form created from the manifest, this info is always needed to create a new
        # account. Check if there is anything that needs to be filled
        form = self.manifest.get("form", [])

        # extra items that are needed from the integration (often prefilled by admin)
        extra_user_info = self.manifest.get("extra_user_info", [])
        needs_more_info = any(
            item["id"] not in user.extra_fields.keys() for item in extra_user_info
        )

        return len(form) > 0 or needs_more_info

    def revoke_user(self, user):
        if self.skip_user_provisioning:
            # should never be triggered
            return False, "Cannot revoke manual integration"

        self.new_hire = user
        self.has_user_context = True

        # Renew token if necessary
        if not self.renew_key():
            return False, "Couldn't renew key"

        revoke_manifest = self.manifest.get("revoke", [])

        # add extra fields directly to params
        self.params = self.new_hire.extra_fields
        self.tracker = IntegrationTracker.objects.create(category=IntegrationTracker.Category.REVOKE, integration=self, for_user=self.new_hire)

        for item in revoke_manifest:
            success, response = self.run_request(item)

            if not success:
                return False, self.clean_response(response)

        return True, ""

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
            if hasattr(self, "tracker"):
                # we need to clean the last step as we now probably got new secret keys that need to be masked
                last_step = self.tracker.steps.last()
                last_step.json_response = self.clean_response(last_step.json_response)
                last_step.save()

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

    def execute(self, new_hire=None, params=None):
        self.params = params or {}
        self.params["responses"] = []
        self.params["files"] = {}
        self.new_hire = new_hire
        self.has_user_context = new_hire is not None

        self.tracker = IntegrationTracker.objects.create(category=IntegrationTracker.Category.EXECUTE, integration=self, for_user=self.new_hire)

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
            success, response = self.run_request(item)

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
            if not success:
                if self.has_user_context:
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
            save_as_file = item.get("save_as_file")
            if save_as_file is not None:
                self.params["files"][save_as_file] = io.BytesIO(response.content)

            # save json response temporarily to be reused in other parts
            try:
                self.params["responses"].append(response.json())
            except:  # noqa E722
                # if we save a file, then just append an empty dict
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
        if self.skip_user_provisioning:
            from .forms import ManualIntegrationConfigForm

            return ManualIntegrationConfigForm(data=data)

        from .forms import IntegrationConfigForm

        return IntegrationConfigForm(instance=self, data=data)

    def clean_response(self, response) -> str:
        try:
            response = json.dumps(response)
        except:
            response = str(response)

        for name, value in self.extra_args.items():
            response = response.replace(
                str(value), _("***Secret value for %(name)s***") % {"name": name}
            )

        return response

    objects = IntegrationManager()


@receiver(post_delete, sender=Integration)
def delete_schedule(sender, instance, **kwargs):
    Schedule.objects.filter(name=instance.schedule_name).delete()
