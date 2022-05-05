import pyotp
import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from admin.integrations.models import Integration
from admin.templates.forms import UploadField
from organization.models import Organization, WelcomeMessage


class OrganizationGeneralForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        label=_("Timezone"), choices=[(x, x) for x in pytz.common_timezones]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["logo"].required = False

        layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("language"),
                    Field("timezone"),
                    Field("new_hire_email"),
                    Field("new_hire_email_reminders"),
                    Field("new_hire_email_overdue_reminders"),
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
        if Integration.objects.filter(integration=3).exists():
            layout[0][0].extend(
                [
                    Field("google_login"),
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
            and Integration.objects.filter(integration=3).exists()
        ):
            google_login = self.cleaned_data["google_login"]

        if not any([credentials_login, google_login]):
            raise ValidationError(_("You must enable at least one login option"))
        return self.cleaned_data


class SlackSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slack_confirm_person"].required = False

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
            Submit(name="submit", value="Update"),
        )

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
        ]


class AdministratorsCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsCreateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, _("Administrator")), (2, _("Manager")))

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
            "message": _(
                "You can use &#123;&#123; first_name &#125;&#125;, "
                "&#123;&#123; last_name &#125;&#125;, &#123;&#123; position "
                "&#125;&#125;, &#123;&#123; manager &#125;&#125;, and &#123;&#123; "
                "buddy &#125;&#125; in the editor. It will be replaced by the values "
                "corresponding to the new hire."
            )
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
