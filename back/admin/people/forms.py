from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from admin.integrations.models import Integration
from admin.sequences.models import Sequence
from admin.templates.forms import (
    ModelChoiceFieldWithCreate,
    MultiSelectField,
    UploadField,
)
from organization.models import Organization
from users.models import Department, ROLE_CHOICES


class NewHireAddForm(forms.ModelForm):
    sequences = forms.ModelMultipleChoiceField(
        queryset=Sequence.objects.all(),
        to_field_name="id",
        initial=Sequence.objects.filter(auto_add=True),
        required=False,
        label=_("Sequences"),
    )
    buddy = forms.ModelChoiceField(
        queryset=get_user_model().managers_and_admins_or_slack_users.all(),
        label=_("Buddy"),
    )
    manager = forms.ModelChoiceField(
        queryset=get_user_model().managers_and_admins_or_slack_users.all(),
        label=_("Manager"),
    )
    start_day = forms.DateField(
        label=_("Start date"),
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
    )
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["buddy"].required = False
        self.fields["manager"].required = False
        self.fields["department"].required = False
        self.fields["profile_image"].required = False
        self.fields["language"].initial = Organization.object.get().language
        self.fields["timezone"].initial = Organization.object.get().timezone
        self.fields["start_day"].initial = timezone.now().date()
        self.helper = FormHelper()
        layout = Layout(
            Div(
                Div(
                    Field("first_name"),
                    css_class="col-6",
                ),
                Div(
                    Field("last_name"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("email"),
                    css_class="col-6",
                ),
                Div(
                    Field("phone"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("position"),
                    css_class="col-6",
                ),
                Div(
                    Field("start_day"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("timezone"),
                    css_class="col-6",
                ),
                Div(Field("language"), css_class="col-6"),
                css_class="row",
            ),
            Div(
                Div(Field("department", css_class="add"), css_class="col-6"),
                Div(
                    UploadField(
                        "profile_image",
                        extra_context={"file": self.instance.profile_image},
                    ),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("buddy"),
                    css_class="col-6",
                ),
                Div(Field("manager"), css_class="col-6"),
                css_class="row",
            ),
            Div(MultiSelectField("sequences"), css_class="row"),
            Submit(name="submit", value=_("Create new hire")),
        )
        # Only show if the slack bot has been enabled
        if Integration.objects.filter(integration=Integration.Type.SLACK_BOT).exists():
            layout[2].extend(
                [
                    Div(
                        Div(Field("message"), css_class="col-12"),
                        css_class="row",
                    ),
                ]
            )
        self.helper.layout = layout

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
            "department",
            "profile_image",
        )


class NewHireProfileForm(forms.ModelForm):
    start_day = forms.DateField(
        label=_("Start date"),
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
    )
    buddy = forms.ModelChoiceField(
        queryset=get_user_model().managers_and_admins_or_slack_users.all(),
        label=_("Buddy"),
        required=False,
    )
    manager = forms.ModelChoiceField(
        queryset=get_user_model().managers_and_admins_or_slack_users.all(),
        required=False,
        label=_("Manager"),
    )
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["department"].required = False
        self.fields["profile_image"].required = False
        if self.instance is not None:
            # Fallback option: we are now filtering on admins and managers, but people
            # might have already used an old buddy/manager that is now not in the list
            # anymore. Adding them to the list to not mess with existing data.
            if self.instance.buddy is not None:
                self.fields["buddy"].queryset |= get_user_model().objects.filter(
                    id=self.instance.buddy.id
                )
            if self.instance.manager is not None:
                self.fields["manager"].queryset |= get_user_model().objects.filter(
                    id=self.instance.manager.id
                )
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
                Div(Field("department", css_class="add"), css_class="col-6"),
                Div(
                    UploadField(
                        "profile_image",
                        extra_context={"file": self.instance.profile_image},
                    ),
                    css_class="col-6",
                ),
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
            "department",
            "profile_image",
        )


class ColleagueUpdateForm(forms.ModelForm):
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name", required=False
    )
    birthday = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
        required=False,
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
                Div(Field("birthday"), css_class="col-12"),
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
            "birthday",
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
    department = ModelChoiceFieldWithCreate(
        queryset=Department.objects.all(), to_field_name="name", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["profile_image"].required = False
        self.fields["timezone"].initial = Organization.objects.get().timezone
        self.fields["language"].initial = Organization.objects.get().language
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
        choices=[("email", _("Send via email")), ("text", _("Send via text"))]
    )
    email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if Twillio is not configured, then auto select email and make it disabled
        if settings.TWILIO_ACCOUNT_SID == "":
            self.fields["send_type"].initial = "email"
            self.fields["send_type"].choices = [("email", _("Send via email"))]

    def clean(self):
        cleaned_data = super(PreboardingSendForm, self).clean()
        send_type = cleaned_data.get("send_type")
        email = cleaned_data.get("email", "")
        if send_type == "email" and email in [None, ""]:
            self.add_error("email", _("This field is required"))
        return cleaned_data

    class Meta:
        labels = {
            "send_type": _("Send type"),
        }


class EmailIgnoreForm(forms.Form):
    email = forms.EmailField()


class UserRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].label = ""
        self.fields["role"].help_text = ""
        self.fields["role"].choices = tuple(x for x in ROLE_CHOICES if x[0] != 0)

    class Meta:
        model = get_user_model()
        fields = ("role",)
