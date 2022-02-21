from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms

from django.utils.translation import gettext_lazy as _
from admin.templates.forms import MultiSelectField, UploadField, WYSIWYGField
from organization.models import Tag

from .models import Badge


class BadgeForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        label=_("Tags"), queryset=Tag.objects.all(), to_field_name="name", required=False
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
                    UploadField("image", extra_context={"file": self.instance.image}),
                    css_class="col-4",
                ),
                Div(WYSIWYGField("content"), css_class="col-8"),
                css_class="row",
            ),
        )

    class Meta:
        model = Badge
        exclude = ("template",)

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
