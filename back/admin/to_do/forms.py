from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Row, Column, Div

from misc.fields import ContentFormField
from .models import ToDo

from crispy_forms.layout import Field


class WYSIWYGField(Field):
    template = 'wysiwyg_field.html'


class ToDoForm(forms.ModelForm):
    content = WYSIWYGField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('name'),
                    Field('due_on_day'),
                    Field('tags'),
                    css_class='col-4'
                ),
                Div(
                    WYSIWYGField('content'),
                    css_class='col-8'
                ),
                css_class='row'
            ),
        )

    class Meta:
        model = ToDo
        exclude = ('template',)


