import pyotp
import pytz
from crispy_forms.bootstrap import Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    ButtonHolder,
    Column,
    Div,
    Field,
    Fieldset,
    Layout,
    Submit,
    HTML,
)
from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError

from admin.to_do.forms import UploadField
from organization.models import Organization, WelcomeMessage
from slack_bot.models import SlackChannel


class OrganizationGeneralForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])
    slack_default_channel = forms.ModelChoiceField(queryset=SlackChannel.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("language"),
                    Field("timezone"),
                    Field("new_hire_email"),
                    Field("new_hire_email_reminders"),
                    Field("new_hire_email_overdue_reminders"),
                    HTML("<h3 class='card-title mt-3'>Login options</h3>"),
                    Field("credentials_login"),
                    Field("google_login"),
                    Field("slack_login"),
                    css_class="col-6",
                ),
                Div(
                    UploadField("logo", extra_context={"file": self.instance.logo}),
                    Field("base_color"),
                    Field("accent_color"),
                    Field("bot_color"),
                    Field("slack_buttons"),
                    Field("ask_colleague_welcome_message"),
                    Field("send_new_hire_start_reminder"),
                    Field("auto_create_user"),
                    Field("create_new_hire_without_confirm"),
                    Field("slack_default_channel"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update"),
        )

    class Meta:
        model = Organization
        fields = [
            "name",
            "language",
            "timezone",
            "base_color",
            "accent_color",
            "bot_color",
            "logo",
            "new_hire_email",
            "new_hire_email_reminders",
            "new_hire_email_overdue_reminders",
            "slack_buttons",
            "ask_colleague_welcome_message",
            "send_new_hire_start_reminder",
            "auto_create_user",
            "create_new_hire_without_confirm",
            "credentials_login",
            "google_login",
            "slack_login",
            "slack_default_channel",
        ]
        labels = {
            "slack_login": "Allow users to login with their Slack account",
            "google_login": "Allow users to login with their Google account",
            "credentials_login": "Allow users to login with their username and password",
            "slack_default_channel": "This is the default channel where the bot will post messages in",
        }

    def clean(self):
        credentials_login = self.cleaned_data["credentials_login"]
        google_login = self.cleaned_data["google_login"]
        slack_login = self.cleaned_data["slack_login"]
        if not any([credentials_login, google_login, slack_login]):
            raise ValidationError("You must enable at least one login option")
        return self.cleaned_data


class AdministratorsCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsCreateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, "Administrator"), (2, "Manager"))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "role"]


class AdministratorsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsUpdateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, "Administrator"), (2, "Manager"))

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
            "message": "You can use {{ first_name }}, {{ last_name }}, {{ position }}, {{ manager }} and {{ buddy }} above. It will be replaced by the values corresponding to the new hire."
        }


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label="6 digit OTP code",
        help_text="This is the code that your 2FA application shows you.",
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
                "OTP token was not correct. Please wait 30 seconds and then try again"
            )

        cache.set(f"{self.user.email}_totp_passed", "true", 30)
        return otp
