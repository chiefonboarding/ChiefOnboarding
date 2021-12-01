from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Div,
    Field,
    Layout,
)
from django import forms

from organization.models import Tag
from admin.to_do.forms import MultiSelectField

from .models import Introduction


class IntroductionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), to_field_name="name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    MultiSelectField("tags"),
                    Field("intro_person"),
                    css_class="col-4",
                ),
                css_class="row",
            ),
        )

    class Meta:
        model = Introduction
        exclude = ("template",)

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
