import pyotp
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView
from twilio.rest import Client
import json
import logging
import smtplib
import traceback
from anymail.exceptions import AnymailAPIError, AnymailInvalidAddress, AnymailRecipientsRefused

from admin.integrations.models import Integration
from organization.models import Notification, Organization, WelcomeMessage
from slack_bot.models import SlackChannel
from slack_bot.utils import Slack, actions, button, paragraph
from users.emails import (
    email_new_admin_cred,
    send_new_hire_credentials,
    send_new_hire_preboarding,
)
from users.mixins import AdminPermMixin, LoginRequiredMixin, ManagerPermMixin

from .forms import (
    AdministratorsCreateForm,
    AdministratorsUpdateForm,
    AISettingsForm,
    EmailSettingsForm,
    OrganizationGeneralForm,
    OTPVerificationForm,
    SlackSettingsForm,
    StorageSettingsForm,
    TestEmailForm,
    WelcomeMessagesUpdateForm,
)


class OrganizationGeneralUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = OrganizationGeneralForm
    success_url = reverse_lazy("settings:general")
    success_message = _("Organization info has been updated")

    def get_object(self):
        return Organization.object.get()

    def form_valid(self, form):
        from admin.sequences.models import Sequence

        selected_sequences = form.cleaned_data["default_sequences"]
        Sequence.objects.all().update(auto_add=False)
        Sequence.objects.filter(id__in=selected_sequences).update(auto_add=True)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("General Updates")
        context["subtitle"] = _("settings")
        return context


class SlackSettingsUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = SlackSettingsForm
    success_url = reverse_lazy("settings:slack")
    success_message = _("Slackbot settings have been updated")

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Slack")
        context["subtitle"] = _("settings")
        return context


class AdministratorListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "settings_admins.html"
    queryset = get_user_model().managers_and_admins.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Administrators")
        context["subtitle"] = _("settings")
        context["add_action"] = reverse_lazy("settings:administrators-create")
        return context


class AdministratorCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "settings_admins_create.html"
    queryset = get_user_model().managers_and_admins.all()
    form_class = AdministratorsCreateForm
    success_url = reverse_lazy("settings:administrators")

    def form_valid(self, form):
        user = get_user_model().objects.filter(email__iexact=form.cleaned_data["email"])
        if user.exists():
            # Change user if user already exists
            user = user.first()
            user.role = form.cleaned_data["role"]
            user.save()
        else:
            user = form.save()
            email_new_admin_cred(user)
        self.object = user

        note_type = (
            Notification.Type.ADDED_ADMIN
            if user.is_admin
            else Notification.Type.ADDED_MANAGER
        )
        Notification.objects.create(
            notification_type=note_type,
            extra_text=user.full_name,
            created_by=self.request.user,
        )
        messages.info(self.request, _("Admin/Manager has been created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Add Administrator")
        context["subtitle"] = _("settings")
        return context


class AdministratorUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "settings_admins_update.html"
    queryset = get_user_model().managers_and_admins.all()
    form_class = AdministratorsUpdateForm
    success_url = reverse_lazy("settings:administrators")
    success_message = _("Admin/Manager has been changed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Change Administrator")
        context["subtitle"] = _("settings")
        return context


class AdministratorDeleteView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, DeleteView
):
    """
    Doesn't actually delete the administrator, it just migrates them to a normal user
    account.
    """

    success_url = reverse_lazy("settings:administrators")
    success_message = _("Admin is now a normal user")

    def get_queryset(self):
        return get_user_model().managers_and_admins.exclude(id=self.request.user.id)

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.role = 3
        self.object.save()
        return HttpResponseRedirect(success_url)


class WelcomeMessageUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_welcome_message_update.html"
    form_class = WelcomeMessagesUpdateForm
    success_message = _("Message has been updated")

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return WelcomeMessage.objects.get(
            language=self.kwargs.get("language"), message_type=self.kwargs.get("type")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["languages"] = settings.LANGUAGES
        context["types"] = WelcomeMessage.Type.choices
        context["title"] = _("Update welcome messages")
        context["subtitle"] = _("settings")
        return context


class WelcomeMessageSendTestMessageView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, View
):
    def post(self, request, **kwargs):
        message_type = self.kwargs.get("type")
        language = self.kwargs.get("language")
        we = get_object_or_404(
            WelcomeMessage,
            language=language,
            message_type=message_type,
        )
        we = request.user.personalize(we.message)
        translation.activate(language)

        if message_type == WelcomeMessage.Type.PREBOARDING:
            send_new_hire_preboarding(
                request.user, email=request.user.email, language=language
            )

        if message_type == WelcomeMessage.Type.NEWHIRE_WELCOME:
            send_new_hire_credentials(
                request.user.id, save_password=False, language=language
            )

        if message_type == WelcomeMessage.Type.TEXT_WELCOME:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=request.user.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=request.user.personalize(we.message),
            )

        if message_type == WelcomeMessage.Type.SLACK_WELCOME:
            Slack().send_message(
                blocks=[paragraph(we)], channel=request.user.slack_user_id
            )

        if message_type == WelcomeMessage.Type.SLACK_KNOWLEDGE:
            blocks = [
                paragraph(we),
                actions(
                    [
                        button(
                            text=_("resources"),
                            value="show_resource_items",
                            style="primary",
                            action_id="show_resource_items",
                        )
                    ]
                ),
            ]

            Slack().send_message(blocks=blocks, channel=request.user.slack_user_id)

        return HttpResponse(headers={"HX-Trigger": "reload-page"})


class PersonalLanguageUpdateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "personal_language_update.html"
    model = get_user_model()
    fields = [
        "language",
    ]
    success_message = _("Your default language has been updated")

    def form_valid(self, form):
        # In case user changed language, then update it
        self.request.session[settings.LANGUAGE_SESSION_KEY] = self.request.user.language
        translation.activate(self.request.user.language)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update your default language")
        context["subtitle"] = _("settings")
        return context


class AISettingsUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = AISettingsForm
    success_url = reverse_lazy("settings:ai-settings")
    success_message = _("AI settings have been updated")

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("AI Content Generation")
        context["subtitle"] = _("settings")
        return context


class StorageSettingsUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = StorageSettingsForm
    success_url = reverse_lazy("settings:storage")
    success_message = _("Storage settings have been updated")

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Media Storage")
        context["subtitle"] = _("settings")

        # Add a button to the migration tool
        context["actions"] = [
            {
                "url": reverse_lazy("settings:storage-migrate"),
                "text": _("Migration Tool"),
                "icon": "arrow-right-arrow-left",
            }
        ]

        return context

    def form_valid(self, form):
        """
        When the form is valid, update the S3 settings in the environment.
        """
        response = super().form_valid(form)

        # Update S3 settings in the environment
        org = self.object
        if org.storage_provider == 's3':
            # Set S3 environment variables
            import os
            os.environ['AWS_S3_ENDPOINT_URL'] = org.s3_endpoint_url
            os.environ['AWS_ACCESS_KEY_ID'] = org.s3_access_key
            os.environ['AWS_SECRET_ACCESS_KEY'] = org.s3_secret_key
            os.environ['AWS_STORAGE_BUCKET_NAME'] = org.s3_bucket_name
            os.environ['AWS_DEFAULT_REGION'] = org.s3_region
        else:
            # Clear S3 environment variables
            import os
            os.environ['AWS_STORAGE_BUCKET_NAME'] = ''

        return response


class StorageMigrationView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "storage_migration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Storage Migration")
        context["subtitle"] = _("settings")

        # Get migration log from session if available
        if 'migration_log' in self.request.session:
            context['migration_log'] = self.request.session['migration_log']
            # Clear the log after displaying it
            del self.request.session['migration_log']
            self.request.session.modified = True

        return context


class StorageMigrateLocalToS3View(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request):
        # Initialize log
        log = [_("Starting migration from local storage to S3...")]

        try:
            # Get organization settings
            org = Organization.object.get()

            # Check if S3 is configured
            if org.storage_provider != 's3' or not org.s3_bucket_name:
                log.append(_("Error: S3 is not configured. Please configure S3 first."))
                request.session['migration_log'] = log
                return redirect('settings:storage-migrate')

            # Import necessary modules
            import os
            from django.conf import settings
            from misc.models import File
            from misc.s3 import S3

            # Initialize S3 client
            s3 = S3()

            # Check if S3 is properly configured
            if not s3.use_s3:
                log.append(_("Error: S3 client could not be initialized. Check your S3 configuration."))
                request.session['migration_log'] = log
                return redirect('settings:storage-migrate')

            # Get all files from the database
            files = File.objects.all()
            log.append(_("Found {} files in the database.").format(len(files)))

            # Get the local storage path
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            local_s3_path = os.path.join(media_root, 'local_s3')

            # Migrate each file
            migrated_count = 0
            error_count = 0

            for file in files:
                try:
                    # Check if the file exists locally
                    local_path = os.path.join(local_s3_path, file.file)
                    if not os.path.exists(local_path):
                        log.append(_("Warning: File not found locally: {}").format(file.file))
                        error_count += 1
                        continue

                    # Upload the file to S3
                    with open(local_path, 'rb') as f:
                        s3.client.put_object(
                            Bucket=org.s3_bucket_name,
                            Key=file.file,
                            Body=f.read()
                        )

                    migrated_count += 1

                    # Log every 10 files
                    if migrated_count % 10 == 0:
                        log.append(_("Migrated {} files...").format(migrated_count))

                except Exception as e:
                    log.append(_("Error migrating file {}: {}").format(file.file, str(e)))
                    error_count += 1

            # Log the final results
            log.append(_("Migration completed. Successfully migrated {} files. Errors: {}.").format(
                migrated_count, error_count
            ))

        except Exception as e:
            log.append(_("Error during migration: {}").format(str(e)))

        # Store the log in the session
        request.session['migration_log'] = log
        return redirect('settings:storage-migrate')


class StorageMigrateS3ToLocalView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request):
        # Initialize log
        log = [_("Starting migration from S3 to local storage...")]

        try:
            # Get organization settings
            org = Organization.object.get()

            # Import necessary modules
            import os
            from django.conf import settings
            from misc.models import File
            from misc.s3 import S3

            # Initialize S3 client with environment variables
            # We need to temporarily set the environment variables to ensure S3 is used
            old_bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')

            if org.storage_provider == 's3' and org.s3_bucket_name:
                # Set S3 environment variables
                os.environ['AWS_S3_ENDPOINT_URL'] = org.s3_endpoint_url
                os.environ['AWS_ACCESS_KEY_ID'] = org.s3_access_key
                os.environ['AWS_SECRET_ACCESS_KEY'] = org.s3_secret_key
                os.environ['AWS_STORAGE_BUCKET_NAME'] = org.s3_bucket_name
                os.environ['AWS_DEFAULT_REGION'] = org.s3_region
            else:
                log.append(_("Error: S3 is not configured. Cannot migrate from S3."))
                request.session['migration_log'] = log
                return redirect('settings:storage-migrate')

            # Initialize S3 client
            s3 = S3()

            # Check if S3 is properly configured
            if not s3.use_s3:
                log.append(_("Error: S3 client could not be initialized. Check your S3 configuration."))
                # Restore environment variable
                os.environ['AWS_STORAGE_BUCKET_NAME'] = old_bucket
                request.session['migration_log'] = log
                return redirect('settings:storage-migrate')

            # Get all files from the database
            files = File.objects.all()
            log.append(_("Found {} files in the database.").format(len(files)))

            # Get the local storage path
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            local_s3_path = os.path.join(media_root, 'local_s3')

            # Ensure the local storage directory exists
            os.makedirs(local_s3_path, exist_ok=True)

            # Migrate each file
            migrated_count = 0
            error_count = 0

            for file in files:
                try:
                    # Create the directory structure
                    file_dir = os.path.dirname(os.path.join(local_s3_path, file.file))
                    os.makedirs(file_dir, exist_ok=True)

                    # Download the file from S3
                    local_path = os.path.join(local_s3_path, file.file)

                    try:
                        s3.client.download_file(
                            Bucket=org.s3_bucket_name,
                            Key=file.file,
                            Filename=local_path
                        )

                        migrated_count += 1

                        # Log every 10 files
                        if migrated_count % 10 == 0:
                            log.append(_("Migrated {} files...").format(migrated_count))

                    except Exception as e:
                        log.append(_("Error downloading file {}: {}").format(file.file, str(e)))
                        error_count += 1

                except Exception as e:
                    log.append(_("Error migrating file {}: {}").format(file.file, str(e)))
                    error_count += 1

            # Log the final results
            log.append(_("Migration completed. Successfully migrated {} files. Errors: {}.").format(
                migrated_count, error_count
            ))

            # Restore environment variable
            os.environ['AWS_STORAGE_BUCKET_NAME'] = old_bucket

        except Exception as e:
            log.append(_("Error during migration: {}").format(str(e)))

        # Store the log in the session
        request.session['migration_log'] = log
        return redirect('settings:storage-migrate')


class EmailSettingsUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = EmailSettingsForm
    success_url = reverse_lazy("settings:email")
    success_message = _("Email settings have been updated")

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Email Settings")
        context["subtitle"] = _("settings")
        return context

    def form_valid(self, form):
        """
        When the form is valid, reload the email settings.
        """
        response = super().form_valid(form)

        # Reload email settings
        from organization.email_config import get_email_backend, get_default_from_email
        from django.conf import settings

        try:
            # Try to get the email backend from the database
            email_backend = get_email_backend()
            if email_backend:
                # Replace the default email backend with our custom one
                settings.EMAIL_BACKEND = email_backend

            # Try to get the default from email from the database
            default_from_email = get_default_from_email()
            if default_from_email:
                # Replace the default from email with our custom one
                settings.DEFAULT_FROM_EMAIL = default_from_email
        except Exception:
            # If there's any error, just use the environment settings
            pass

        return response


class OTPView(LoginRequiredMixin, ManagerPermMixin, FormView):
    template_name = "personal_otp.html"
    form_class = OTPVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.requires_otp = True
        user.save()
        keys = user.reset_otp_recovery_keys()
        return render(
            self.request,
            "personal_otp.html",
            {"title": _("TOTP 2FA"), "subtitle": _("settings"), "keys": keys},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.requires_otp:
            context["otp_url"] = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
                name=user.email, issuer_name="ChiefOnboarding"
            )
        context["title"] = (
            _("Enable TOTP 2FA") if not user.requires_otp else _("TOTP 2FA")
        )
        context["subtitle"] = _("settings")
        return context


class IntegrationsListView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "settings_integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Integrations")
        context["subtitle"] = _("settings")
        context["slack_bot"] = Integration.objects.filter(
            integration=Integration.Type.SLACK_BOT, active=True
        ).first()
        context["google_login"] = Integration.objects.filter(
            integration=Integration.Type.GOOGLE_LOGIN, active=True
        ).first()
        context["slack_bot_environ"] = settings.SLACK_APP_TOKEN != ""
        context["base_url"] = settings.BASE_URL

        context["custom_integrations"] = Integration.objects.filter(
            integration=Integration.Type.CUSTOM, is_active=True
        )
        context["inactive_integrations"] = Integration.inactive.filter(
            integration=Integration.Type.CUSTOM, is_active=False
        )
        context["add_action"] = reverse_lazy("integrations:create")
        context["disable_update_channels_list"] = (
            settings.SLACK_DISABLE_AUTO_UPDATE_CHANNELS
        )
        return context


class SlackBotSetupView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    model = Integration
    fields = [
        "app_id",
        "client_id",
        "client_secret",
        "signing_secret",
        "verification_token",
    ]
    success_message = _(
        "Slack has now been connected, check if you got a message from your bot!"
    )
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Slack bot setup")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Enable")
        return context

    def form_valid(self, form):
        Integration.objects.filter(integration=Integration.Type.SLACK_BOT).delete()
        form.instance.integration = 0
        return super().form_valid(form)


class SlackChannelsUpdateView(LoginRequiredMixin, AdminPermMixin, RedirectView):
    permanent = False
    pattern_name = "settings:integrations"

    def get(self, request, *args, **kwargs):
        if settings.SLACK_DISABLE_AUTO_UPDATE_CHANNELS:
            raise Http404
        SlackChannel.objects.update_channels()
        messages.success(
            request,
            _(
                "Newly added channels have been added. Make sure the bot has been "
                "added to that channel too if you want it to post/get info there!"
            ),
        )
        return super().get(request, *args, **kwargs)


class SlackChannelsCreateView(LoginRequiredMixin, AdminPermMixin, CreateView):
    template_name = "slack_channel_create.html"
    model = SlackChannel
    fields = ["name", "is_private"]
    success_message = _("Slack channel has been added")
    success_url = reverse_lazy("settings:slack-account-add-channel")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Slack channels")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Enable")
        context["channels"] = SlackChannel.objects.all()
        return context


class TestEmailView(LoginRequiredMixin, AdminPermMixin, FormView):
    template_name = "email_test.html"
    form_class = TestEmailForm
    success_url = reverse_lazy("settings:email")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Test Email Configuration")
        context["subtitle"] = _("settings")
        return context

    def form_valid(self, form):
        # Get the form data
        recipient = form.cleaned_data["recipient"]
        subject = form.cleaned_data["subject"]
        message = form.cleaned_data["message"]

        # Create a log to capture the email sending process
        log_entries = []
        log_entries.append(_("Starting email test..."))

        # Get the organization
        org = Organization.object.get()
        log_entries.append(_("Using organization: {}").format(org.name))

        # Get the email configuration
        try:
            # Import the email backend configuration
            from organization.email_config import get_email_backend, get_default_from_email

            # Log the email provider being used
            log_entries.append(_("Email provider: {}").format(org.email_provider or "Default from environment"))

            # Get the email backend
            email_backend = get_email_backend()
            if email_backend:
                log_entries.append(_("Using custom email backend from database settings"))
            else:
                log_entries.append(_("Using default email backend from environment settings: {}").format(settings.EMAIL_BACKEND))

            # Get the from email
            from_email = get_default_from_email()
            log_entries.append(_("From email: {}").format(from_email))

            # Create HTML message
            html_message = org.create_email({
                "org": org,
                "content": [{"type": "paragraph", "data": {"text": message}}],
                "user": self.request.user
            })

            log_entries.append(_("Attempting to send email to: {}").format(recipient))

            # Try to send the email
            try:
                from django.core.mail import send_mail

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient],
                    html_message=html_message,
                    fail_silently=False,
                )

                log_entries.append(_("Email sent successfully!"))
                messages.success(self.request, _("Test email sent successfully to {}").format(recipient))

            except AnymailRecipientsRefused as e:
                error_msg = _("Error: Recipients refused - {}").format(str(e))
                log_entries.append(error_msg)
                messages.error(self.request, error_msg)

            except AnymailAPIError as e:
                error_msg = _("Error: API error - {}").format(str(e))
                log_entries.append(error_msg)
                messages.error(self.request, error_msg)

            except AnymailInvalidAddress as e:
                error_msg = _("Error: Invalid address - {}").format(str(e))
                log_entries.append(error_msg)
                messages.error(self.request, error_msg)

            except smtplib.SMTPException as e:
                error_msg = _("Error: SMTP error - {}").format(str(e))
                log_entries.append(error_msg)
                messages.error(self.request, error_msg)

            except Exception as e:
                error_msg = _("Error: Unexpected error - {}").format(str(e))
                log_entries.append(error_msg)
                log_entries.append(traceback.format_exc())
                messages.error(self.request, error_msg)

        except Exception as e:
            error_msg = _("Error configuring email backend: {}").format(str(e))
            log_entries.append(error_msg)
            log_entries.append(traceback.format_exc())
            messages.error(self.request, error_msg)

        # Store the log in the session for display
        self.request.session['email_test_log'] = log_entries

        return super().form_valid(form)
