import base64
import io
import json
import time
import uuid
from datetime import timedelta
from django.contrib.postgres.fields import ArrayField
from json.decoder import JSONDecodeError as NativeJSONDecodeError

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


class MethodTypes(models.TextChoices):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class IntegrationTracker(models.Model):
    """Model to track the integrations that ran. Gives insights into error messages"""

    class Category(models.IntegerChoices):
        EXECUTE = 0, _("Run the execute part")
        EXISTS = 1, _("Check if user exists")
        REVOKE = 2, _("Revoke user")

    integration = models.ForeignKey(
        "integrations.Integration", on_delete=models.CASCADE, null=True
    )
    category = models.IntegerField(choices=Category.choices)
    for_user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=True)
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
    tracker = models.ForeignKey(
        "integrations.IntegrationTracker",
        on_delete=models.CASCADE,
        related_name="steps",
    )
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
        return super().get_queryset().filter(is_active=True)

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

class IntegrationInactiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=False)


class ManifestExists(models.Model):
    url = models.URLField(max_length=255, default="", blank=True)
    method = models.CharField(choices=MethodTypes.choices, default=MethodTypes.GET, max_length=255)
    expected = models.CharField(max_length=255, verbose_name=_("Expected text in the response"), help_text=_("Either use this or the status code to validate if the user exists"), default="", blank=True)
    status_code = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
        help_text=_("Either use this or the 'expected text' to validate if the user exists")
    )
    headers = models.JSONField(default=list, blank=True, help_text="Without any items, it will use the default")

    @property
    def is_valid(self):
        return self.url != ""


class Manifest(models.Model):
    exists = models.OneToOneField(
        ManifestExists, on_delete=models.CASCADE, null=True
    )
    headers = models.JSONField(default=list, blank=True)
    schedule = models.CharField(default="")


class ManifestRevoke(models.Model):
    manifest = models.ForeignKey(
        Manifest, on_delete=models.CASCADE, null=True, related_name="revoke"
    )
    url = models.URLField(max_length=255)
    method = models.CharField(choices=MethodTypes.choices, default=MethodTypes.GET, max_length=255)
    data = models.JSONField(default=dict)
    expected = models.CharField(default="", max_length=255, blank=True)
    status_code = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True
    )
    headers = models.JSONField(default=list, blank=True, help_text="Without any items, it will use the default")


class ManifestExecute(models.Model):
    manifest = models.ForeignKey(
        Manifest, on_delete=models.CASCADE, null=True, related_name="execute"
    )
    url = models.URLField(max_length=255)
    method = models.CharField(choices=MethodTypes.choices, default=MethodTypes.GET, max_length=255)
    data = models.JSONField(default=dict)
    expected = models.CharField(max_length=255)
    store_data = models.JSONField(default=dict)
    continue_if = models.JSONField(default=dict)
    polling = models.JSONField(default=dict)
    save_as_file = models.CharField(default="", blank=True)
    files = models.JSONField(default=dict)
    headers = models.JSONField(default=list, blank=True)


class ManifestForm(models.Model):
    class ItemsType(models.TextChoices):
        CHOICE = "CHOICE"
        INPUT = "INPUT"

    class OptionsSource(models.TextChoices):
        FIXED_LIST = "fixed list"
        FETCH_URL = "fetch url"

    manifest = models.ForeignKey(
        Manifest, on_delete=models.CASCADE, null=True, related_name="form"
    )
    index_id = models.BigAutoField(primary_key=True)
    id = models.CharField(max_length=100, help_text=_("This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."))
    name = models.CharField(max_length=255, help_text=_("The form label shown to the admin"))
    type = models.CharField(choices=ItemsType.choices, max_length=7, help_text=_("If you choose choice, you will be able to set the options yourself OR fetch from an external url."), default=ItemsType.INPUT)
    options_source = models.CharField(choices=OptionsSource.choices, default=OptionsSource.FIXED_LIST)

    # fixed items
    items = models.JSONField(default=list, help_text=_("Use only if you set type to 'choice'. This is for fixed items (if you don't want to fetch from a URL)"), blank=True)

    # dynamic choices
    url = models.URLField(max_length=255, help_text=_("The url it should fetch the options from."), blank=True)
    method = models.CharField(choices=MethodTypes.choices, default=MethodTypes.GET, max_length=255, verbose_name=_("Request method"))
    data = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, help_text=_("(optionally) This will overwrite the default headers."), blank=True)
    data_from = models.CharField(max_length=255, default="", help_text=_("The property it should use from the response of the url if you need to go deeper into the result."), blank=True)
    choice_value = models.CharField(max_length=255, default="id", help_text=_("The value it should take for using in other parts of the integration"), blank=True)
    choice_name = models.CharField(max_length=255, default="name", help_text=_("The name that should be displayed to the admin as an option."), blank=True)

    def is_input_form_field(self):
        return self.type == ManifestForm.ItemsType.INPUT


class ManifestInitialData(models.Model):
    manifest = models.ForeignKey(
        Manifest, on_delete=models.CASCADE, null=True, related_name="initial_data_form"
    )
    index_id = models.BigAutoField(primary_key=True)
    id = models.CharField(max_length=100, help_text=_("This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."))
    name = models.CharField(max_length=255, help_text=_("Type 'generate' if you want this value to be generated on the fly (different for each execution), will not need to be filled by a user"))
    description = models.CharField(max_length=1255, help_text=_("This will be shown under the input field for extra context"))
    secret = models.BooleanField(default=False, help_text="Enable this if the value should always be masked")


class ManifestExtraUserInfo(models.Model):
    manifest = models.ForeignKey(
        Manifest, on_delete=models.CASCADE, null=True, related_name="extra_user_info"
    )
    index_id = models.BigAutoField(primary_key=True)
    id = models.CharField(max_length=100, help_text=_("This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."))
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1255, help_text=_("This will be shown under the input field for extra context"))


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
        MANUAL_USER_PROVISIONING = (
            3,
            _("Manual user account provisioning, no manifest required"),
        )

    name = models.CharField(max_length=300, default="", blank=True)
    is_active = models.BooleanField(default=True, help_text="If inactive, it's a test/debug integration")
    integration = models.IntegerField(choices=Type.choices)
    manifest_type = models.IntegerField(
        choices=ManifestType.choices, null=True, blank=True
    )
    token = EncryptedTextField(max_length=10000, default="", blank=True)
    refresh_token = EncryptedTextField(max_length=10000, default="", blank=True)
    base_url = models.CharField(max_length=22300, default="", blank=True)
    redirect_url = models.CharField(max_length=22300, default="", blank=True)
    account_id = models.CharField(max_length=22300, default="", blank=True)
    active = models.BooleanField(default=True) # legacy?
    ttl = models.IntegerField(null=True, blank=True)
    expiring = models.DateTimeField(auto_now_add=True, blank=True)
    one_time_auth_code = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )

    manifest_obj = models.OneToOneField(Manifest, null=True, on_delete=models.CASCADE)
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
        return self.manifest_obj.revoke.exists()

    @property
    def update_url(self):
        return reverse("integrations:update", args=[self.id])

    def get_icon_template(self):
        return render_to_string("_integration_config.html")

    @property
    def schedule_name(self):
        return f"User sync for integration: {self.id}"

    @property
    def secret_values(self):
        return ManifestInitialData.objects.filter(manifest=self.manifest_obj, secret=True).exclude(name="generate")

    @property
    def missing_secret_values(self):
        return self.secret_values.exclude(id__in=self.extra_args.keys())

    @property
    def filled_secret_values(self):
        return self.secret_values.filter(id__in=self.extra_args.keys())

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
        schedule_cron = self.manifest_obj.schedule

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

    @property
    def has_oauth(self):
        return "oauth" in self.manifest

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

        self.tracker = IntegrationTracker.objects.create(
            category=IntegrationTracker.Category.EXISTS,
            integration=self,
            for_user=new_hire,
        )

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

    def test_user_exists(self, new_hire):
        self.new_hire = new_hire
        self.has_user_context = new_hire is not None

        # Renew token if necessary
        if not self.renew_key():
            return _("Couldn't renew token")

        success, response = self.run_request(self.manifest["exists"])

        if isinstance(response, str):
            return _("Error when making the request: %(error)s") % {"error": response}

        user_exists = (
            self._replace_vars(self.manifest["exists"]["expected"]) in response.text
        )

        found_user = "FOUND USER" if user_exists else "COULD NOT FIND USER"

        return f"{found_user} in {response.text}"

    def needs_user_info(self, user):
        if self.skip_user_provisioning:
            return False

        # form created from the manifest, this info is always needed to create a new
        # account. Check if there is anything that needs to be filled
        form_items = ManifestForm.objects.filter(manifest__integration=self).count()

        # extra items that are needed from the integration (often prefilled by admin)
        extra_user_info = ManifestExtraUserInfo.objects.filter(manifest__integration=self).values_list("id", flat=True)
        needs_more_info = any(
            item not in user.extra_fields.keys() for item in extra_user_info
        )

        return form_items > 0 or needs_more_info

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
        self.tracker = IntegrationTracker.objects.create(
            category=IntegrationTracker.Category.REVOKE,
            integration=self if self.pk is not None else None,
            for_user=self.new_hire,
        )

        for item in revoke_manifest:
            success, response = self.run_request(item)

            if not success:
                return False, self.clean_response(response)

        return True, ""

    def execute(self, new_hire=None, params=None, retry_on_failure=False):
        self.params = params or {}
        self.params["responses"] = []
        self.params["files"] = {}
        self.new_hire = new_hire
        self.has_user_context = new_hire is not None

        self.tracker = IntegrationTracker.objects.create(
            category=IntegrationTracker.Category.EXECUTE,
            integration=self if self.pk is not None else None,
            for_user=self.new_hire,
        )

        # Renew token if necessary
        if not self.renew_key():
            return False, None



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

    objects = IntegrationManager()
    inactive = IntegrationInactiveManager()


@receiver(post_delete, sender=Integration)
def delete_schedule(sender, instance, **kwargs):
    Schedule.objects.filter(name=instance.schedule_name).delete()
