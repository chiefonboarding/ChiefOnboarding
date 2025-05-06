import pyotp
import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_q.models import Schedule

from admin.integrations.models import Integration
from admin.templates.forms import UploadField
from organization.models import Organization, WelcomeMessage


class OrganizationGeneralForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        label=_("Timezone"), choices=[(x, x) for x in pytz.common_timezones]
    )
    default_sequences = forms.ModelMultipleChoiceField(
        label=_("Sequences that are preselected for all new hires:"),
        queryset=None,
        to_field_name="id",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Avoid circular import
        from admin.sequences.models import Sequence

        self.helper = FormHelper()
        self.fields["logo"].required = False
        self.fields["custom_email_template"].required = False
        self.fields["default_sequences"].queryset = Sequence.objects.all()
        self.fields["default_sequences"].initial = Sequence.objects.filter(
            auto_add=True
        )

        layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("language"),
                    Field("timezone"),
                    Field("new_hire_email"),
                    Field("new_hire_email_reminders"),
                    Field("new_hire_email_overdue_reminders"),
                    Field("default_sequences"),
                    HTML("<h3 class='card-title mt-3'>" + _("Login options") + "</h3>"),
                    Field("credentials_login"),
                    css_class="col-6",
                ),
                Div(
                    UploadField("logo", extra_context={"file": self.instance.logo}),
                    Field("base_color"),
                    Field("accent_color"),
                    Field("custom_email_template"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update"),
        )
        self.helper.layout = layout

        # Only show if google login has been enabled
        if Integration.objects.filter(
            integration=Integration.Type.GOOGLE_LOGIN
        ).exists():
            layout[0][0].extend(
                [
                    Field("google_login"),
                ]
            )
        # Only show if OIDC client has been enabled
        if settings.OIDC_CLIENT_ID:
            layout[0][0].extend(
                [
                    Field("oidc_login"),
                ]
            )

    class Meta:
        model = Organization
        fields = [
            "name",
            "language",
            "timezone",
            "base_color",
            "accent_color",
            "logo",
            "google_login",
            "oidc_login",
            "new_hire_email",
            "new_hire_email_reminders",
            "new_hire_email_overdue_reminders",
            "credentials_login",
            "custom_email_template",
        ]

    def clean(self):
        credentials_login = self.cleaned_data["credentials_login"]
        google_login = False
        if (
            "google_login" in self.cleaned_data
            and Integration.objects.filter(
                integration=Integration.Type.GOOGLE_LOGIN
            ).exists()
        ):
            google_login = self.cleaned_data["google_login"]
        oidc_login = self.cleaned_data.get("oidc_login", False)
        if not any([credentials_login, google_login, oidc_login]):
            raise ValidationError(_("You must enable at least one login option"))
        return self.cleaned_data


class SlackSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slack_confirm_person"].required = False
        self.fields["slack_birthday_wishes_channel"].required = False

        auto_create_new_hire_class = ""
        if not self.instance.auto_create_user:
            auto_create_new_hire_class = "d-none"

        auto_create_without_confirm_class = ""
        if self.instance.create_new_hire_without_confirm:
            auto_create_without_confirm_class = "d-none"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("bot_color"),
            Field("slack_buttons"),
            Field("ask_colleague_welcome_message"),
            Field("send_new_hire_start_reminder"),
            Field("slack_default_channel"),
            Field("auto_create_user"),
            Div(
                Field("create_new_hire_without_confirm"),
                Div(
                    Field("slack_confirm_person"),
                    css_class=auto_create_without_confirm_class,
                ),
                css_class=auto_create_new_hire_class,
            ),
            Field("slack_birthday_wishes_channel"),
            Submit(name="submit", value="Update"),
        )

    def save(self, commit=True):
        slack_settings = super().save(commit=commit)
        slack_settings.save()

        # Add birthday schedule if not exists but should be there (just got enabled)
        if (
            slack_settings.slack_birthday_wishes_channel is not None
            and not Schedule.objects.filter(name="birthday_reminder").exists()
        ):
            Schedule.objects.create(
                func="slack_bot.tasks.birthday_reminder",
                name="birthday_reminder",
                schedule_type=Schedule.DAILY,
            )

        # Remove birthday schedule if channel got set to None
        if (
            slack_settings.slack_birthday_wishes_channel is None
            and Schedule.objects.filter(name="birthday_reminder").exists()
        ):
            Schedule.objects.filter(
                name="birthday_reminder",
            ).delete()

        return slack_settings

    class Meta:
        model = Organization
        fields = [
            "bot_color",
            "slack_buttons",
            "ask_colleague_welcome_message",
            "send_new_hire_start_reminder",
            "slack_default_channel",
            "auto_create_user",
            "create_new_hire_without_confirm",
            "slack_confirm_person",
            "slack_birthday_wishes_channel",
        ]


class AdministratorsCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsCreateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, _("Administrator")), (2, _("Manager")))

    def validate_unique(self):
        pass

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "role"]


class AdministratorsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsUpdateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, _("Administrator")), (2, _("Manager")))

    class Meta:
        model = get_user_model()
        fields = [
            "role",
        ]


class WelcomeMessagesUpdateForm(forms.ModelForm):
    class Meta:
        model = WelcomeMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea,
        }
        help_texts = {
            "message": mark_safe(
                _(
                    "You can use &#123;&#123; first_name &#125;&#125;, "
                    "&#123;&#123; last_name &#125;&#125;, &#123;&#123; position "
                    "&#125;&#125;, &#123;&#123; department &#125;&#125;, &#123;&#123; "
                    "manager &#125;&#125;, and &#123;&#123; "
                    "buddy &#125;&#125; in the editor. It will be replaced by the "
                    "values corresponding to the new hire."
                )
            )
        }


class AISettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("ai_api_key"),
            Field("ai_default_context"),
            Field("ai_default_tone"),
            Submit(name="submit", value="Update"),
        )

    class Meta:
        model = Organization
        fields = [
            "ai_api_key",
            "ai_default_context",
            "ai_default_tone",
        ]
        widgets = {
            "ai_api_key": forms.PasswordInput(render_value=True),
            "ai_default_context": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "ai_api_key": _("API key for AI content generation (e.g., OpenAI API key)"),
            "ai_default_context": _("Default context for AI content generation (e.g., 'You are writing content for an employee onboarding platform')"),
            "ai_default_tone": _("Default tone for AI content generation (e.g., 'professional', 'friendly', 'casual')"),
        }


class EmailSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        # Create the base layout
        self.helper.layout = Layout(
            HTML("<h3 class='card-title'>" + _("Email Notifications") + "</h3>"),
            Field("new_hire_email"),
            Field("new_hire_email_reminders"),
            Field("new_hire_email_overdue_reminders"),
            Field("email_admin_task_notifications"),
            Field("email_admin_task_comments"),
            Field("email_admin_updates"),

            HTML("<h3 class='card-title mt-4'>" + _("Email Customization") + "</h3>"),
            Field("email_from_name"),
            Field("email_signature"),
            Field("custom_email_template"),

            HTML("<h3 class='card-title mt-4'>" + _("Email Provider Configuration") + "</h3>"),
            Field("email_provider"),
            Field("default_from_email"),

            # SMTP Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("SMTP Settings") + "</h4>"),
                Field("email_host"),
                Field("email_port"),
                Field("email_host_user"),
                Field("email_host_password"),
                Field("email_use_tls"),
                Field("email_use_ssl"),
                css_class="email-provider-settings smtp-settings",
            ),

            # Mailgun Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("Mailgun Settings") + "</h4>"),
                Field("mailgun_api_key"),
                Field("mailgun_domain"),
                css_class="email-provider-settings mailgun-settings",
            ),

            # Mailjet Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("Mailjet Settings") + "</h4>"),
                Field("mailjet_api_key"),
                Field("mailjet_secret_key"),
                css_class="email-provider-settings mailjet-settings",
            ),

            # Mandrill Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("Mandrill Settings") + "</h4>"),
                Field("mandrill_api_key"),
                css_class="email-provider-settings mandrill-settings",
            ),

            # Postmark Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("Postmark Settings") + "</h4>"),
                Field("postmark_server_token"),
                css_class="email-provider-settings postmark-settings",
            ),

            # SendGrid Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("SendGrid Settings") + "</h4>"),
                Field("sendgrid_api_key"),
                css_class="email-provider-settings sendgrid-settings",
            ),

            # Sendinblue Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("Sendinblue Settings") + "</h4>"),
                Field("sendinblue_api_key"),
                css_class="email-provider-settings sendinblue-settings",
            ),

            # MailerSend Settings
            Div(
                HTML("<h4 class='card-subtitle mt-3'>" + _("MailerSend Settings") + "</h4>"),
                Field("mailersend_api_key"),
                css_class="email-provider-settings mailersend-settings",
            ),

            HTML("""
            <script>
                // Wacht tot het document volledig geladen is
                window.addEventListener('load', function() {
                    // Zoek het email provider selectieveld
                    const providerSelect = document.getElementById('id_email_provider');
                    if (!providerSelect) {
                        console.error('Email provider select field not found');
                        return;
                    }

                    // Zoek alle provider-specifieke instellingen
                    const allSettings = document.querySelectorAll('.email-provider-settings');
                    if (allSettings.length === 0) {
                        console.error('Provider settings not found');
                        return;
                    }

                    console.log('Found ' + allSettings.length + ' provider settings sections');

                    function updateVisibleSettings() {
                        console.log('Updating visible settings for provider: ' + providerSelect.value);

                        // Verberg eerst alle instellingen
                        allSettings.forEach(el => {
                            el.style.display = 'none';
                            console.log('Hiding: ' + el.className);
                        });

                        // Toon de instellingen voor de geselecteerde provider
                        const selectedProvider = providerSelect.value;
                        if (selectedProvider) {
                            const selectedSettings = document.querySelector('.' + selectedProvider + '-settings');
                            if (selectedSettings) {
                                console.log('Showing: ' + selectedSettings.className);
                                selectedSettings.style.display = 'block';
                            } else {
                                console.error('Settings for provider ' + selectedProvider + ' not found');
                            }
                        }
                    }

                    // Voer de update direct uit
                    updateVisibleSettings();

                    // Update wanneer de selectie verandert
                    providerSelect.addEventListener('change', updateVisibleSettings);

                    // Voeg een knop toe om de instellingen handmatig te vernieuwen
                    const refreshButton = document.createElement('button');
                    refreshButton.type = 'button';
                    refreshButton.className = 'btn btn-sm btn-secondary mt-2';
                    refreshButton.textContent = 'Vernieuw velden';
                    refreshButton.onclick = updateVisibleSettings;

                    // Voeg de knop toe na het selectieveld
                    providerSelect.parentNode.appendChild(refreshButton);
                });
            </script>
            """),

            Submit(name="submit", value="Update"),
        )

    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get('email_provider')

        # Validate that the required fields for the selected provider are filled
        if provider == 'smtp':
            if not cleaned_data.get('email_host'):
                self.add_error('email_host', _('SMTP Host is required when using SMTP'))
            if not cleaned_data.get('email_port'):
                self.add_error('email_port', _('SMTP Port is required when using SMTP'))
        elif provider == 'mailgun':
            if not cleaned_data.get('mailgun_api_key'):
                self.add_error('mailgun_api_key', _('API Key is required when using Mailgun'))
            if not cleaned_data.get('mailgun_domain'):
                self.add_error('mailgun_domain', _('Domain is required when using Mailgun'))
        elif provider == 'mailjet':
            if not cleaned_data.get('mailjet_api_key'):
                self.add_error('mailjet_api_key', _('API Key is required when using Mailjet'))
            if not cleaned_data.get('mailjet_secret_key'):
                self.add_error('mailjet_secret_key', _('Secret Key is required when using Mailjet'))
        elif provider == 'mandrill':
            if not cleaned_data.get('mandrill_api_key'):
                self.add_error('mandrill_api_key', _('API Key is required when using Mandrill'))
        elif provider == 'postmark':
            if not cleaned_data.get('postmark_server_token'):
                self.add_error('postmark_server_token', _('Server Token is required when using Postmark'))
        elif provider == 'sendgrid':
            if not cleaned_data.get('sendgrid_api_key'):
                self.add_error('sendgrid_api_key', _('API Key is required when using SendGrid'))
        elif provider == 'sendinblue':
            if not cleaned_data.get('sendinblue_api_key'):
                self.add_error('sendinblue_api_key', _('API Key is required when using Sendinblue'))
        elif provider == 'mailersend':
            if not cleaned_data.get('mailersend_api_key'):
                self.add_error('mailersend_api_key', _('API Key is required when using MailerSend'))

        # Validate that both TLS and SSL are not enabled at the same time for SMTP
        if provider == 'smtp' and cleaned_data.get('email_use_tls') and cleaned_data.get('email_use_ssl'):
            self.add_error('email_use_tls', _('You cannot enable both TLS and SSL at the same time'))
            self.add_error('email_use_ssl', _('You cannot enable both TLS and SSL at the same time'))

        return cleaned_data

    class Meta:
        model = Organization
        fields = [
            # Email notifications
            "new_hire_email",
            "new_hire_email_reminders",
            "new_hire_email_overdue_reminders",
            "email_admin_task_notifications",
            "email_admin_task_comments",
            "email_admin_updates",

            # Email customization
            "email_from_name",
            "email_signature",
            "custom_email_template",

            # Email provider configuration
            "email_provider",
            "default_from_email",

            # SMTP settings
            "email_host",
            "email_port",
            "email_host_user",
            "email_host_password",
            "email_use_tls",
            "email_use_ssl",

            # Provider-specific settings
            "mailgun_api_key",
            "mailgun_domain",
            "mailjet_api_key",
            "mailjet_secret_key",
            "mandrill_api_key",
            "postmark_server_token",
            "sendgrid_api_key",
            "sendinblue_api_key",
            "mailersend_api_key",
        ]
        widgets = {
            "email_signature": forms.Textarea(attrs={"rows": 4}),
            "custom_email_template": forms.Textarea(attrs={"rows": 10}),
            "email_host_password": forms.PasswordInput(render_value=True),
            "mailgun_api_key": forms.PasswordInput(render_value=True),
            "mailjet_api_key": forms.PasswordInput(render_value=True),
            "mailjet_secret_key": forms.PasswordInput(render_value=True),
            "mandrill_api_key": forms.PasswordInput(render_value=True),
            "postmark_server_token": forms.PasswordInput(render_value=True),
            "sendgrid_api_key": forms.PasswordInput(render_value=True),
            "sendinblue_api_key": forms.PasswordInput(render_value=True),
            "mailersend_api_key": forms.PasswordInput(render_value=True),
        }
        help_texts = {
            # Email customization help texts
            "email_from_name": _("If left empty, the default from email address from your environment settings will be used."),
            "email_signature": _("This signature will be added to all outgoing emails. HTML is supported."),
            "custom_email_template": _(
                "Leave blank to use the default template. "
                "See documentation if you want to use your own."
            ),

            # Email provider help texts
            "email_provider": _("Select which email provider to use for sending emails"),
            "default_from_email": _("The email address that will be used as the sender (e.g., 'onboarding@yourcompany.com' or 'Your Company <onboarding@yourcompany.com>')"),

            # SMTP help texts
            "email_host": _("SMTP server hostname (e.g., 'smtp.gmail.com')"),
            "email_port": _("SMTP server port (usually 25, 465, or 587)"),
            "email_host_user": _("SMTP server username"),
            "email_host_password": _("SMTP server password"),
            "email_use_tls": _("Use TLS encryption for SMTP connection"),
            "email_use_ssl": _("Use SSL encryption for SMTP connection (don't enable both TLS and SSL)"),
        }


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label=_("6 digit OTP code"),
        help_text=_("This is the code that your 2FA application shows you."),
        max_length=6,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_otp(self):
        otp = self.cleaned_data["otp"]
        totp = pyotp.TOTP(self.user.totp_secret)
        valid = totp.verify(otp)
        # Check if token is correct and block replay attacks
        if not valid and cache.get(f"{self.user.email}_totp_passed") is None:
            raise ValidationError(
                _(
                    "OTP token was not correct. Please wait 30 seconds and then try "
                    "again"
                )
            )

        cache.set(f"{self.user.email}_totp_passed", "true", 30)
        return otp
