from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.core.exceptions import ValidationError

from admin.to_do.forms import MultiSelectField
from admin.to_do.models import ToDo

from .models import Condition


class ConditionCreateForm(forms.ModelForm):
    condition_to_do = forms.ModelMultipleChoiceField(
        queryset=ToDo.templates.all(), to_field_name="id", required=False
    )

    def _get_save_button(self):
        return '<button hx-post="{% url "sequences:condition-create" object.id %}" hx-target="#condition_form" hx-swap="#add-condition-form" class="btn btn-primary ms-auto">Add block</button>'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        is_time_condition = (
            self.instance.condition_type in [0, 2] or self.instance == None
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
        labels = {
            "condition_to_do": "Trigger after these to do items have been completed:",
            "condition_type": "Block type",
            "days": "Amount of days before/after new hire has started",
            "time": "At",
        }
        widgets = {
            "time": forms.TimeInput(attrs={"type": "time", "step": 300}),
        }
        help_texts = {
            "time": "Must be in a 5 minute interval.",
        }

    def clean_days(self):
        day = self.cleaned_data["days"]
        if day == 0 and self.cleaned_data["condition_type"] in [0, 2]:
            raise ValidationError(
                "You cannot use 0. The day before starting is 1 and the first workday is 1"
            )

        return day

    def clean_time(self):
        time = self.cleaned_data["time"]
        if time.minute % 10 not in [0, 5] and self.cleaned_data["condition_type"] in [
            0,
            2,
        ]:
            raise ValidationError(
                f"Time must be in an interval of 5 minutes. {time.minute} must end in 0 or 5."
            )

        return time

    def clean(self):
        cleaned_data = super().clean()
        condition_type = cleaned_data.get("condition_type", None)
        time = cleaned_data.get("time", None)
        days = cleaned_data.get("days", None)
        condition_to_do = cleaned_data.get("condition_to_do", None)
        if condition_type == 1 and condition_to_do == None:
            raise ValidationError("You must add at least one to do item")
        if condition_type in [0, 2] and (time is None or days is None):
            raise ValidationError("Both the time and days have to be filled in.")
        return cleaned_data


class ConditionUpdateForm(ConditionCreateForm):
    def _get_save_button(self):
        return '<button hx-post="{% url "sequences:condition-update" object.id condition.id %}" hx-target="#condition_form" hx-swap="#add-condition-form" class="btn btn-primary ms-auto">Edit block</button>'


class ConditionToDoUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiSelectField("condition_to_do"),
        )

    class Meta:
        model = Condition
        fields = [
            "condition_to_do",
        ]
