from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import MultiSelectField, TagModelForm, WYSIWYGField

from .models import Appointment


class AppointmentForm(TagModelForm):
    content = WYSIWYGField()
    date = forms.DateField(label=_("Date"), required=True, widget=forms.DateInput(attrs={"type": "date"}, format=('%Y-%m-%d')))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        fixed_date = self.instance.fixed_date
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

    class Meta:
        model = Appointment
        exclude = ("template",)
        widgets = {
            "time": forms.TimeInput(attrs={"type": "time", "step": 300}),
        }
