import pyotp
from crispy_forms.bootstrap import Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Div, Field, Fieldset, Layout, Row, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from organization.models import Organization, WelcomeMessage
from admin.to_do.forms import UploadField


class OrganizationGeneralForm(forms.ModelForm):
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
                    css_class="col-6",
                ),
                Div(
                    UploadField("logo", extra_context={'file': self.instance.logo}),
                    Field("base_color"),
                    Field("accent_color"),
                    Field("bot_color"),
                    Field("slack_buttons"),
                    Field("ask_colleague_welcome_message"),
                    Field("send_new_hire_start_reminder"),
                    Field("auto_create_user"),
                    Field("create_new_hire_without_confirm"),
                    css_class="col-6"
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update")
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
        ]


class AdministratorsCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsCreateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = ((1, "Administrator"), (2, "Manager"))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "role"]


class WelcomeMessagesUpdateForm(forms.ModelForm):
    class Meta:
        model = WelcomeMessage
        fields = ["message"]


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
        if not valid:
            raise ValidationError("OTP token was not correct. Please try again")
        return otp
