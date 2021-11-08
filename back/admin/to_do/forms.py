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
    content = WYSIWYGField()
    tags = forms.ModelChoiceField(queryset=Tag.objects.all(), to_field_name="name", empty_label=None)

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
                Div(WYSIWYGField("content"), css_class="col-8"),
                css_class="row",
            ),
        )

    class Meta:
        model = ToDo
        exclude = ("template",)
