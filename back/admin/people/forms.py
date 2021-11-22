from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Div, Field, Fieldset, Layout, Row, Submit
from django import forms
from django.contrib.auth import get_user_model


class NewHireProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("first_name"),
                    Field("email"),
                    Field("position"),
                    css_class="col-6"
                ),
                Div(
                    Field("last_name"),
                    Field("phone"),
                    Field("start_day"),
                    css_class="col-6"
                ),
                css_class="row",
            ),
            Div(
                Div(Field("message"), css_class="col-12"),
                css_class="row",
            ),
            Div(
                Div(
                    Field("timezone"),
                    Field("buddy"),
                    css_class="col-6",
                ),
                Div(
                    Field("language"),
                    Field("manager"),
                    css_class="col-6"
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update")
        )

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "position", "email", "phone", "start_day", "message", "timezone", "language", "buddy", "manager")


class ColleagueUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("first_name"),
                    css_class="col-6"
                ),
                Div(
                    Field("last_name"),
                    css_class="col-6"
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("email"),
                    css_class="col-12"
                ),
                Div(
                    Field("position"),
                    css_class="col-12"
                ),
                Div(
                    Field("phone"),
                    css_class="col-12"
                ),
                Div(
                    Field("message"),
                    css_class="col-12"
                ),
                Div(
                    Field("facebook"),
                    css_class="col-12"
                ),
                Div(
                    Field("linkedin"),
                    css_class="col-12"
                ),
                Div(
                    Field("timezone"),
                    css_class="col-12"
                ),
                Div(
                    Field("language"),
                    css_class="col-12"
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update")
        )

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "position", "email", "phone", "message", "facebook", "twitter", "linkedin", "timezone", "language")

