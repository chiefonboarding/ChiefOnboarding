from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import ugettext_lazy as _

from admin.templates.forms import MultiSelectField, WYSIWYGField
from admin.templates.forms import TagModelForm

from .models import Preboarding


class PreboardingForm(TagModelForm):

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
