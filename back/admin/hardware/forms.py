from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django.utils.translation import gettext_lazy as _

from admin.hardware.models import Hardware
from admin.templates.forms import MultiSelectField, TagModelForm, WYSIWYGField


class HardwareForm(TagModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Check if assigned_to field should be hidden
        hide_assigned_to = "d-none"
        if self.data.get("person_type", None) == str(Hardware.PersonType.CUSTOM) or (
            self.instance is not None
            and self.instance.person_type == Hardware.PersonType.CUSTOM
        ):
            hide_assigned_to = ""

        layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("departments"),
                    Field("person_type"),
                    Div(
                        Field("assigned_to"),
                        css_class=hide_assigned_to,
                    ),
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
        self.helper.layout = layout

    class Meta:
        model = Hardware
        fields = ("name", "person_type", "assigned_to", "tags", "content", "departments")

    def clean(self):
        cleaned_data = super().clean()
        assigned_to = cleaned_data.get("assigned_to")
        person_type = cleaned_data["person_type"]
        if person_type == Hardware.PersonType.CUSTOM and assigned_to is None:
            self.add_error("assigned_to", _("This field is required"))
        return cleaned_data
