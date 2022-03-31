from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import MultiSelectField, TagModelForm, WYSIWYGField

from .models import Appointment


class AppointmentForm(TagModelForm):
    content = WYSIWYGField()
    date = forms.DateField(
        label=_("Date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        fixed_date = self.instance.fixed_date or (
            "fixed_date" in self.data and self.data["fixed_date"] == "on"
        )
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    MultiSelectField("tags"),
                    Field("fixed_date"),
                    Div(
                        Field("on_day"),
                        css_class="d-none" if fixed_date else "",
                    ),
                    Div(
                        Field("date"),
                        Field("time"),
                        css_class="" if fixed_date else "d-none",
                    ),
                    css_class="col-4",
                ),
                Div(WYSIWYGField("content"), css_class="col-8"),
                css_class="row",
            ),
        )

    def clean(self):
        cleaned_data = super(AppointmentForm, self).clean()
        fixed_date = cleaned_data.get("fixed_date")
        on_day = cleaned_data.get("on_day")
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")
        if not fixed_date and not on_day:
            self.add_error(
                "on_day", _("Please select a channel to send the message to")
            )
        if fixed_date:
            if not date:
                self.add_error("date", _("This field is required"))
            if not time:
                self.add_error("time", _("This field is required"))
        return cleaned_data

    class Meta:
        model = Appointment
        exclude = ("template",)
        widgets = {
            "time": forms.TimeInput(attrs={"type": "time", "step": 300}),
        }
