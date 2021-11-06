from crispy_forms.helper import FormHelper
from django.contrib.auth import get_user_model
from django import forms

from organization.models import Organization, WelcomeMessage

from crispy_forms.bootstrap import Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Row, Column, Div, Field


class OrganizationGeneralForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ["name", "language", "timezone", "base_color", "accent_color", "bot_color", "logo", "new_hire_email", "new_hire_email_reminders", "new_hire_email_overdue_reminders", "slack_buttons", "ask_colleague_welcome_message", "send_new_hire_start_reminder", "auto_create_user", "create_new_hire_without_confirm"]


class AdministratorsCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdministratorsCreateForm, self).__init__(*args, **kwargs)
        self.fields['role'].choices = ((1, "Administrator"), (2, "Manager"))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "role"]


class WelcomeMessagesUpdateForm(forms.ModelForm):
    class Meta:
        model = WelcomeMessage
        fields = ["message"]
