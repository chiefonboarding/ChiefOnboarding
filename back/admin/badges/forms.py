from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import (MultiSelectField, TagModelForm, UploadField,
                                   WYSIWYGField)

from .models import Badge


class BadgeForm(TagModelForm):
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
