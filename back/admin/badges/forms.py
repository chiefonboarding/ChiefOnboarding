from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Div,
    Field,
    Layout,
)
from crispy_forms.utils import TEMPLATE_PACK
from django import forms

from organization.models import Tag
from admin.to_do.forms import UploadField, WYSIWYGField, MultiSelectField

from .models import Badge


class BadgeForm(forms.ModelForm):
    content_json = WYSIWYGField(label="content")
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), to_field_name="name", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    MultiSelectField("tags"),
                    UploadField("image", extra_context={"file": self.instance.image}),
                    css_class="col-4",
                ),
                Div(WYSIWYGField("content_json"), css_class="col-8"),
                css_class="row",
            ),
        )

    class Meta:
        model = Badge
        exclude = ("template",)

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
