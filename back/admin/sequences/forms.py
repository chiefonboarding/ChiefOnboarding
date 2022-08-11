from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import MultiSelectField, WYSIWYGField
from admin.to_do.models import ToDo
from users.models import User

from .models import (
    PEOPLE_CHOICES_WITH_CHANNELS,
    PEOPLE_CHOICES,
    Condition,
    PendingAdminTask,
    PendingEmailMessage,
    PendingSlackMessage,
    PendingTextMessage,
)


class ConditionCreateForm(forms.ModelForm):
    condition_to_do = forms.ModelMultipleChoiceField(
        queryset=ToDo.templates.all().defer("content"),
        to_field_name="id",
        required=False,
    )

    def _get_save_button(self):
        return (
            (
                '<button hx-post="{% url "sequences:condition-create" object.id %}" '
                'hx-target="#condition_form" hx-swap="#condition_form" '
                'class="btn btn-primary ms-auto">'
            )
            + _("Add block")
            + "</button>"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        is_time_condition = (
            self.instance.condition_type in [0, 2] or self.instance is None
        )
        self.helper.layout = Layout(
            Field("condition_type"),
            Div(
                MultiSelectField("condition_to_do"),
                css_class="d-none" if is_time_condition else "",
            ),
            Div(
                Field("days"),
                Field("time"),
                css_class="" if is_time_condition else "d-none",
            ),
            HTML(self._get_save_button()),
        )
        self.fields["time"].required = False
        self.fields["days"].required = False
        self.fields["condition_to_do"].required = False
        # Remove last option, which will only be one of
        self.fields["condition_type"].choices = tuple(
            x for x in Condition.CONDITION_TYPE if x[0] != 3
        )

    class Meta:
        model = Condition
        fields = ["condition_type", "days", "time", "condition_to_do"]
        widgets = {
            "time": forms.TimeInput(attrs={"type": "time", "step": 300}),
        }
        help_texts = {
            "time": _("Must be in a 5 minute interval."),
        }

    def clean_days(self):
        day = self.cleaned_data["days"]
        if day is None:
            # Handled in clean() function
            return day
        if self.cleaned_data["condition_type"] in [0, 2] and day <= 0:
            raise ValidationError(
                _(
                    "You cannot use 0 or less. The day before starting is 1 and the "
                    "first workday is 1"
                )
            )

        return day

    def clean_time(self):
        time = self.cleaned_data["time"]
        if time is None:
            # Handled in clean() function
            return time
        if time.minute % 10 not in [0, 5] and self.cleaned_data["condition_type"] in [
            0,
            2,
        ]:
            raise ValidationError(
                _(
                    "Time must be in an interval of 5 minutes. %(minutes)s must end in "
                    "0 or 5."
                )
                % {"minutes": time.minute}
            )

        return time

    def clean(self):
        cleaned_data = super().clean()
        condition_type = cleaned_data.get("condition_type", None)
        time = cleaned_data.get("time", None)
        days = cleaned_data.get("days", None)
        condition_to_do = cleaned_data.get("condition_to_do", None)
        if condition_type == 1 and (
            condition_to_do is None or len(condition_to_do) == 0
        ):
            raise ValidationError(_("You must add at least one to do item"))
        if condition_type in [0, 2] and (time is None or days is None):
            raise ValidationError(_("Both the time and days have to be filled in."))
        return cleaned_data


class ConditionUpdateForm(ConditionCreateForm):
    def _get_save_button(self):
        return (
            (
                '<button hx-post="{% url "sequences:condition-update" object.id '
                'condition.id %}" hx-target="#condition_form" '
                'hx-swap="#add-condition-form" class="btn btn-primary ms-auto">'
            )
            + _("Edit block")
            + "</button>"
        )


class PendingAdminTaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.managers_and_admins.all(), required=False
    )
    slack_user = forms.ModelChoiceField(
        queryset=User.objects.exclude(slack_user_id=""),
        required=False,
    )
    date = forms.DateField(
        label=_("Due date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option"].initial = 0
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Check if assigned_to field should be hidden
        hide_assigned_to = "d-none"
        if self.instance is not None and self.instance.person_type == 3:
            hide_assigned_to = ""

        self.helper.layout = Layout(
            Div(
                Field("name"),
                Field("person_type"),
                Div(
                    Field("assigned_to"),
                    css_class=hide_assigned_to,
                ),
                Field("date"),
                Field("priority"),
                Field("comment"),
                Field("option"),
                Field("slack_user"),
                Field("email"),
            ),
        )

    class Meta:
        model = PendingAdminTask
        fields = [
            "name",
            "person_type",
            "assigned_to",
            "date",
            "priority",
            "comment",
            "option",
            "slack_user",
            "email",
        ]


class PendingSlackMessageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Check if send_to field should be hidden
        hide_send_to = "d-none"
        if self.instance is not None and self.instance.person_type == 3:
            hide_send_to = ""

        hide_send_to_channel = "d-none"
        if self.instance is not None and self.instance.person_type == 4:
            hide_send_to_channel = ""

        self.helper.layout = Layout(
            Div(
                Field("name"),
                WYSIWYGField("content_json"),
                Field("person_type"),
                Div(
                    Field("send_to"),
                    css_class=hide_send_to,
                ),
                Div(
                    Field("send_to_channel"),
                    css_class=hide_send_to_channel,
                ),
            ),
        )

    class Meta:
        model = PendingSlackMessage
        fields = [
            "name",
            "content_json",
            "person_type",
            "send_to",
            "send_to_channel",
        ]


class PendingTextMessageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Check if send_to field should be hidden
        hide_send_to = "d-none"
        if self.instance is not None and self.instance.person_type == 3:
            hide_send_to = ""

        # Remove the Slack channel options
        self.fields["person_type"].choices = PEOPLE_CHOICES
        self.fields["person_type"].widget.choices = PEOPLE_CHOICES

        self.helper.layout = Layout(
            Div(
                Field("name"),
                Field("content"),
                Field("person_type"),
                Div(
                    Field("send_to"),
                    css_class=hide_send_to,
                ),
            ),
        )

    class Meta:
        model = PendingTextMessage
        fields = [
            "name",
            "content",
            "person_type",
            "send_to",
        ]


class PendingEmailMessageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Check if send_to field should be hidden
        hide_send_to = "d-none"
        if self.instance is not None and self.instance.person_type == 3:
            hide_send_to = ""

        # Remove the Slack channel options
        self.fields["person_type"].choices = PEOPLE_CHOICES
        self.fields["person_type"].widget.choices = PEOPLE_CHOICES

        self.helper.layout = Layout(
            Div(
                Field("name"),
                Field("subject"),
                WYSIWYGField("content_json"),
                Field("person_type"),
                Div(
                    Field("send_to"),
                    css_class=hide_send_to,
                ),
            ),
        )

    class Meta:
        model = PendingEmailMessage
        fields = [
            "name",
            "subject",
            "content_json",
            "person_type",
            "send_to",
        ]
