from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from crispy_forms.utils import TEMPLATE_PACK
from django import forms

from admin.templates.forms import MultiSelectField, WYSIWYGField
from organization.models import Tag

from .models import Preboarding


class PreboardingForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), to_field_name="name"
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
                    css_class="col-4",
                ),
                Div(WYSIWYGField("content"), css_class="col-8"),
                css_class="row",
            ),
        )

    class Meta:
        model = Preboarding
        exclude = ("template", "picture")

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
