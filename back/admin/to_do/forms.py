from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms

from organization.models import Tag

from .models import ToDo
from admin.templates.forms import WYSIWYGField, MultiSelectField



class ToDoForm(forms.ModelForm):
    content_json = WYSIWYGField(label="content")
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), to_field_name="name", required=False
    )

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
                    WYSIWYGField("content_json"),
                    Field("send_back"),
                    Div(
                        Field("slack_channel"),
                        css_class="d-none slack_channel_dissapear"
                    ),
                    css_class="col-8",
                ),
                css_class="row",
            ),
        )

    class Meta:
        model = ToDo
        exclude = ("template", "form", "content")

        labels = {
            "send_back": "Post new hire's answers from form (if applicable) back to Slack channel"
        }
        help_texts = {
            "send_back": "Let your new hire now that the answers are going to be shared with the team!"
        }

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
