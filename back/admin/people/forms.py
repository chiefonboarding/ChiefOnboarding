import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Div,
    Field,
    Layout,
    Submit,
)
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from admin.sequences.models import Sequence
from admin.templates.forms import MultiSelectField, UploadField
from users.models import Department
from django.conf import settings


class NewHireAddForm(forms.ModelForm):
    sequences = forms.ModelMultipleChoiceField(
        queryset=Sequence.objects.all(), to_field_name="id", required=False
    )
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])
    start_day = forms.DateField(required=True)

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
            Div(MultiSelectField("sequences"), css_class="row"),
            Submit(name="submit", value="Create new hire"),
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
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])

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
            Submit(name="submit", value="Update"),
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


class ModelChoiceFieldWithCreate(forms.ModelChoiceField):
    def prepare_value(self, value):
        # Forcing pk value in this case. Otherwise "selected" will not work
        if hasattr(value, "_meta"):
            return value.pk
        return super().prepare_value(value)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"
            if isinstance(value, self.queryset.model):
                value = getattr(value, key)
            value = self.queryset.get(**{key: value})
        except (ValueError, TypeError) as e:
            print(e)
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        except self.queryset.model.DoesNotExist:
            value = self.queryset.create(**{key: value})
        return value


class ColleagueUpdateForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.common_timezones])
    department = ModelChoiceFieldWithCreate(queryset=Department.objects.all(), to_field_name="name")

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
    department = ModelChoiceFieldWithCreate(queryset=Department.objects.all(), to_field_name="name")

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
    sequences = forms.ModelMultipleChoiceField(label="Select sequences you want to add ", widget=forms.CheckboxSelectMultiple, queryset=Sequence.objects.all())


class PreboardingSendForm(forms.Form):
    send_type = forms.ChoiceField(choices=[("text", "Send via text"), ("email", "Send via email")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if Twillio is not configured, then auto select text and make it disabled
        if settings.TWILIO_ACCOUNT_SID == "":
            self.fields['send_type'].widget.attrs['disabled'] = 'true'
            self.fields['send_type'].initial = 'text'

