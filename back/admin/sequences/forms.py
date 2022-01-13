from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Div,
    Field,
    Layout,
    HTML,
)
from crispy_forms.utils import TEMPLATE_PACK
from django import forms
from django.core.exceptions import ValidationError

from organization.models import Tag

from admin.to_do.forms import MultiSelectField

from .models import Condition


class ConditionCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("condition_type"),
            MultiSelectField("condition_to_do"),
            Field("days"),
            Field("time"),
            HTML('<button hx-post="{% url "sequences:condition-create" object.id %}" hx-target="#condition_form" hx-swap="none" class="btn btn-primary ms-auto">Add block</button>')
        )
        self.fields['time'].required = False
        self.fields['days'].required = False
        # self.fields["role"].choices = Condition.CONDITION_TYPE.pop(-1)


    class Meta:
        model = Condition
        fields = ["condition_type", "days", "time", "condition_to_do"]
        labels = {
            'condition_to_do': 'Trigger after these to do items have been completed:',
            'condition_type': 'Block type',
            'days': 'Amount of days before/after new hire has started',
            'time': 'At',
        }
        widgets = {
            'time': forms.TimeInput(attrs={'type':'time', 'step': 300}),
        }
        help_texts = {
            'time': 'Must be in a 5 minute interval.',
        }

    def clean_days(self):
        day = self.cleaned_data['days']
        if day == 0 and self.cleaned_data['condition_type'] in [0,2]:
            raise ValidationError("You cannot use 0. The day before starting is 1 and the first workday is 1")

        return day

    def clean_time(self):
        time = self.cleaned_data['time']
        if time.minute % 10 not in [0, 5] and self.cleaned_data['condition_type'] in [0,2]:
            raise ValidationError(f"Time must be in an interval of 5 minutes. {time.minute} must end in 0 or 5.")

        return time

    def clean(self):
        condition_type = self.cleaned_data['condition_type']
        if condition_type == 1 and self.cleaned_data['condition_to_do'] == None:
            raise ValidationError("You must add at least one to do item")
        if condition_type in [0, 2] and (self.cleaned_data['time'] is None or self.cleaned_data['days'] is None):
            raise ValidationError("Both the time and days have to be filled in.")
        return self.cleaned_data


class ConditionToDoUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiSelectField("condition_to_do"),
        )

    class Meta:
        model = Condition
        fields = ["condition_to_do",]
