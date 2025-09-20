from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import gettext_lazy as _

from admin.integrations.models import Integration
from admin.templates.forms import MultiSelectField, TagModelForm, WYSIWYGField

from .models import ToDo


class ToDoForm(TagModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["slack_channel"].required = False

        send_back_class = "d-none "
        if (self.instance is not None and self.instance.send_back) or (
            "send_back" in self.data and self.data["send_back"] == "on"
        ):
            send_back_class = ""

        layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("due_on_day"),
                    Field("departments"),
                    MultiSelectField("tags"),
                    css_class="col-4",
                ),
                Div(
                    WYSIWYGField("content"),
                    css_class="col-8",
                ),
                css_class="row",
            ),
        )
        # Only show if the slack bot has been enabled
        if Integration.objects.filter(integration=Integration.Type.SLACK_BOT).exists():
            layout[0][1].extend(
                [
                    Field("send_back"),
                    Div(
                        Field("slack_channel"),
                        css_class=send_back_class + "slack_channel_dissapear",
                    ),
                ]
            )
        self.helper.layout = layout

    def clean(self):
        cleaned_data = super(ToDoForm, self).clean()
        send_back = cleaned_data.get("send_back")
        slack_channel = cleaned_data.get("slack_channel", None)
        if send_back and slack_channel is None:
            self.add_error(
                "slack_channel", _("Please select a channel to send the message to")
            )
        return cleaned_data

    class Meta:
        model = ToDo
        fields = (
            "content",
            "due_on_day",
            "send_back",
            "slack_channel",
            "tags",
            "departments",
            "name",
        )
        help_texts = {
            "send_back": _(
                "Let your new hire now that the answers are going to be shared with the"
                " team!"
            )
        }
