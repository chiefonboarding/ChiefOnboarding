import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from admin.sequences.models import Sequence
from admin.templates.forms import (ModelChoiceFieldWithCreate,
                                   MultiSelectField, UploadField)
from users.models import Department


class NewHireAddForm(forms.ModelForm):
    sequences = forms.ModelMultipleChoiceField(
        queryset=Sequence.objects.all(),
        to_field_name="id",
        required=False,
        label=_("Sequences"),
    )
    timezone = forms.ChoiceField(
        label=_("Timezone"), choices=[(x, x) for x in pytz.common_timezones]
    )
    start_day = forms.DateField(label=_("Start date"), required=True)

    def __init__(self, *args, **kwargs):
        from organization.models import Organization

        super().__init__(*args, **kwargs)
        self.fields["buddy"].required = False
        self.fields["manager"].required = False
        self.fields["language"].initial = Organization.objects.get().language
        self.fields["timezone"].initial = Organization.objects.get().timezone
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("first_name"),
                    Field("email"),
                    Field("position"),
                    css_class="col-6",
                ),
                Div(
                    Field("last_name"),
                    Field("phone"),
                    Field("start_day"),
                    css_class="col-6",
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
                Div(Field("language"), Field("manager"), css_class="col-6"),
                css_class="row",
            ),
            Div(MultiSelectField("sequences"), css_class="row"),
            Submit(name="submit", value=_("Create new hire")),
        )

    class Meta:
        model = get_user_model()
        fields = (
            "first_name",
            "last_name",
            "position",
            "email",
            "phone",
            "start_day",
            "message",
            "timezone",
            "language",
            "buddy",
            "manager",
        )


class NewHireProfileForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        label=_("Timezone"), choices=[(x, x) for x in pytz.common_timezones]
    )
    start_day = forms.DateField(label=_("Start date"), required=True, widget=forms.DateInput(attrs={"type": "date"}, format=('%Y-%m-%d')))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("first_name"),
                    Field("email"),
                    Field("position"),
                    css_class="col-6",
                ),
                Div(
                    Field("last_name"),
                    Field("phone"),
                    Field("start_day"),
                    css_class="col-6",
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
                Div(Field("language"), Field("manager"), css_class="col-6"),
                css_class="row",
            ),
            Submit(name="submit", value=_("Update")),
        )

    class Meta:
        model = get_user_model()
        fields = (
            "first_name",
            "last_name",
            "position",
            "email",
            "phone",
            "start_day",
            "message",
            "timezone",
            "language",
            "buddy",
            "manager",
        )


class ColleagueUpdateForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_image"].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("first_name"), css_class="col-6"),
                Div(Field("last_name"), css_class="col-6"),
                css_class="row",
            ),
            Div(
                Div(Field("email"), css_class="col-12"),
                Div(Field("position"), css_class="col-12"),
                Div(Field("department", css_class="add"), css_class="col-12"),
                Div(Field("phone"), css_class="col-12"),
                Div(Field("message"), css_class="col-12"),
                Div(Field("facebook"), css_class="col-12"),
                Div(Field("linkedin"), css_class="col-12"),
                Div(Field("timezone"), css_class="col-12"),
                Div(Field("language"), css_class="col-12"),
                UploadField(
                    "profile_image", extra_context={"file": self.instance.profile_image}
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Update"),
        )

    class Meta:
        model = get_user_model()
        fields = (
            "first_name",
            "last_name",
            "position",
            "department",
            "email",
            "phone",
            "message",
            "facebook",
            "twitter",
            "linkedin",
            "timezone",
            "language",
            "profile_image",
        )


class ColleagueCreateForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["profile_image"].required = False
        self.helper.layout = Layout(
            Div(
                Div(Field("first_name"), css_class="col-6"),
                Div(Field("last_name"), css_class="col-6"),
                css_class="row",
            ),
            Div(
                Div(Field("email"), css_class="col-12"),
                Div(Field("position"), css_class="col-12"),
                Div(Field("department", css_class="add"), css_class="col-12"),
                Div(Field("phone"), css_class="col-12"),
                Div(Field("message"), css_class="col-12"),
                Div(Field("facebook"), css_class="col-12"),
                Div(Field("linkedin"), css_class="col-12"),
                Div(Field("timezone"), css_class="col-12"),
                Div(Field("language"), css_class="col-12"),
                UploadField(
                    "profile_image", extra_context={"file": self.instance.profile_image}
                ),
                css_class="row",
            ),
            Submit(name="submit", value="Create"),
        )

    class Meta:
        model = get_user_model()
        fields = (
            "first_name",
            "last_name",
            "position",
            "department",
            "email",
            "phone",
            "message",
            "facebook",
            "twitter",
            "linkedin",
            "timezone",
            "language",
            "profile_image",
        )


class SequenceChoiceForm(forms.Form):
    sequences = forms.ModelMultipleChoiceField(
        label=_("Select sequences you want to add "),
        widget=forms.CheckboxSelectMultiple,
        queryset=Sequence.objects.all(),
    )


class RemindMessageForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].initial = _("This task has just been reopened! ")

    message = forms.CharField(
        label=_("Message that you want to leave for your new hire:"),
        widget=forms.Textarea,
        max_length=1200,
    )


class PreboardingSendForm(forms.Form):
    send_type = forms.ChoiceField(
        choices=[("text", _("Send via text")), ("email", _("Send via email"))]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if Twillio is not configured, then auto select text and make it disabled
        if settings.TWILIO_ACCOUNT_SID == "":
            self.fields["send_type"].widget.attrs["disabled"] = "true"
            self.fields["send_type"].initial = "text"

    class Meta:
        labels = {
            "send_type": _("Send type"),
        }
