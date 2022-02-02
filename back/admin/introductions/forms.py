from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.template.loader import render_to_string

from admin.templates.forms import MultiSelectField
from organization.models import Tag

from .models import Introduction


class IntroductionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), to_field_name="name", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    MultiSelectField("tags"),
                    Field("intro_person"),
                    css_class="col-12",
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
