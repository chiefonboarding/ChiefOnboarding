from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Div, Field, Fieldset, Layout, Row, Submit
from django import forms

from misc.fields import ContentFormField
from organization.models import Tag

from .models import ToDo


class WYSIWYGField(Field):
    template = "wysiwyg_field.html"


class MultiSelectField(Field):
    template = "multi_select_field.html"


class ToDoForm(forms.ModelForm):
    content_json = WYSIWYGField(label="content")
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), to_field_name="name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("due_on_day"),
                    MultiSelectField("tags"),
                    css_class="col-4",
                ),
                Div(WYSIWYGField("content_json"), css_class="col-8"),
                css_class="row",
            ),
        )

    class Meta:
        model = ToDo
        exclude = ("template", "form", "content")

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        return [tag.name for tag in tags]
