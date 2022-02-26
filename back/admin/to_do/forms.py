from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import MultiSelectField, TagModelForm, WYSIWYGField

from .models import ToDo


class ToDoForm(TagModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("due_on_day"),
                    MultiSelectField("tags"),
                    css_class="col-4",
                ),
                Div(
                    WYSIWYGField("content"),
                    Field("send_back"),
                    Div(
                        Field("slack_channel"),
                        css_class="d-none slack_channel_dissapear",
                    ),
                    css_class="col-8",
                ),
                css_class="row",
            ),
        )

    class Meta:
        model = ToDo
        exclude = ("template", "form")
        help_texts = {
            "send_back": _(
                "Let your new hire now that the answers are going to be shared with the team!"
            )
        }
