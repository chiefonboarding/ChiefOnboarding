import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_q.models import Schedule

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

    class Meta:
        model = Organization
        fields = [
            "name",
            "language",
            "timezone",
            "base_color",
            "accent_color",
            "logo",
            "new_hire_email",
            "new_hire_email_reminders",
            "new_hire_email_overdue_reminders",
            "custom_email_template",
        ]


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
        fields = ["first_name", "last_name", "email", "role", "departments"]


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
