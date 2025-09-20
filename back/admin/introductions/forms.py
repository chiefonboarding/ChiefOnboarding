from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout

from admin.templates.forms import MultiSelectField, TagModelForm

from .models import Introduction


class IntroductionForm(TagModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("departments"),
                    MultiSelectField("tags"),
                    Field("intro_person"),
                    css_class="col-12",
                ),
                css_class="row",
            ),
        )

    class Meta:
        model = Introduction
        fields = ("intro_person", "name", "tags", "departments")
