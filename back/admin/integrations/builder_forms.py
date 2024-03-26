from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.utils.translation import gettext_lazy as _

from admin.integrations.utils import (
    convert_array_to_object,
    prepare_initial_data,
)
from admin.integrations.validators import (
    validate_continue_if,
    validate_ID,
    validate_polling,
    validate_status_code,
)
from admin.templates.forms import FieldWithExtraContext


class JSONToDict(forms.JSONField):
    def clean(self, value):
        value = super().clean(value)
        if isinstance(value, list):
            value = convert_array_to_object(value)
        return value


class ValueKeyArrayField(FieldWithExtraContext):
    template = "value_key_array_field.html"


class IntegerListField(FieldWithExtraContext):
    template = "manifest_test/integer_list_field.html"


class ManifestFormForm(forms.Form):
    id = forms.CharField(
        label="ID",
        help_text=_(
            "This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."
        ),
        validators=[validate_ID],
    )
    name = forms.CharField(
        label="Name", help_text=_("The form label shown to the admin")
    )
    type = forms.ChoiceField(
        choices=(("choice", "choice"), ("input", "input")),
        label="Type",
        help_text=_(
            "If you choose choice, you will be able to set the options yourself OR fetch from an external url."
        ),
    )
    options_source = forms.ChoiceField(
        choices=(("fixed list", "fixed list"), ("fetch url", "fetch url")),
        initial="fixed list",
    )

    # fixed items
    items = forms.JSONField(
        initial=list,
        help_text=_(
            "Use only if you set type to 'choice'. This is for fixed items (if you don't want to fetch from a URL)"
        ),
        required=False,
    )

    # dynamic choices
    url = forms.URLField(
        max_length=255,
        help_text=_("The url it should fetch the options from."),
        required=False,
    )
    method = forms.ChoiceField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ),
        initial="GET",
        label=_("Request method"),
    )
    data = forms.JSONField(initial=dict, required=False)
    cast_data_to_json = forms.BooleanField(
        initial=True,
        help_text=_(
            "Check this if the data should be send as json. When unchecked, it's send as a string."
        ),
        required=False,
    )
    headers = JSONToDict(
        initial=list,
        help_text=_("(optionally) This will overwrite the default headers."),
        required=False,
    )
    data_from = forms.CharField(
        max_length=255,
        initial="",
        help_text=_(
            "The property it should use from the response of the url if you need to go deeper into the result."
        ),
        required=False,
    )
    choice_value = forms.CharField(
        max_length=255,
        initial="id",
        help_text=_(
            "The value it should take for using in other parts of the integration"
        ),
        required=False,
    )
    choice_name = forms.CharField(
        max_length=255,
        initial="name",
        help_text=_("The name that should be displayed to the admin as an option."),
        required=False,
    )

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.initial = prepare_initial_data(self.initial)

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        show_manual_items = "d-none"
        show_fetch_url = ""
        show_choice_options = ""
        if self.initial.get("options_source", "fixed list") == "fixed list":
            show_manual_items = ""
            show_fetch_url = "d-none"

        if self.initial.get("type", "") == "input":
            show_choice_options = "d-none"

        self.helper.layout = Layout(
            Div(
                Div(Field("id"), css_class="col-6"),
                Div(Field("name"), css_class="col-6"),
                css_class="row",
            ),
            Div(
                Div(Field("type"), css_class="col-6"),
                Div(Field("options_source"), css_class=f"col-6 {show_choice_options}"),
                css_class="row",
            ),
            Div(
                ValueKeyArrayField("items", extra_context={"disabled": disabled}),
                css_class=f"manual_items {show_manual_items} {show_choice_options}",
            ),
            Div(
                Div(
                    Div(Field("method"), css_class="col-3"),
                    Div(Field("url"), css_class="col-9"),
                    css_class="row",
                ),
                Div(Field("data_from")),
                Div(Field("data")),
                Div(Field("cast_data_to_json")),
                Div(
                    Div(Field("choice_value"), css_class="col-6"),
                    Div(Field("choice_name"), css_class="col-6"),
                    css_class="row",
                ),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
                css_class=f"fetch_items {show_fetch_url} {show_choice_options}",
            ),
        )


class ManifestRevokeForm(forms.Form):
    url = forms.URLField(
        max_length=255,
        help_text=_("The url it should fetch the options from."),
        required=False,
    )
    method = forms.ChoiceField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ),
        initial="GET",
        label=_("Request method"),
        required=False,
    )
    data = forms.JSONField(initial=dict, required=False)
    cast_data_to_json = forms.BooleanField(
        initial=True,
        help_text=_(
            "Check this if the data should be send as json. When unchecked, it's send as a string."
        ),
        required=False,
    )
    expected = forms.CharField(initial="", required=False)
    status_code = SimpleArrayField(
        forms.CharField(max_length=1000), required=False, initial=list
    )
    headers = JSONToDict(
        initial=list,
        help_text=_("(optionally) This will overwrite the default headers."),
        required=False,
    )

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.initial = prepare_initial_data(self.initial)

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(Field("method"), css_class="col-3"),
                    Div(Field("url"), css_class="col-9"),
                    css_class="row",
                ),
                Div(Field("data")),
                Div(Field("cast_data_to_json")),
                Div(Field("expected")),
                IntegerListField("status_code", extra_context={"disabled": disabled}),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
            )
        )


class ManifestHeadersForm(forms.Form):
    headers = forms.JSONField(
        initial=list,
        help_text=_("(optionally) This will overwrite the default headers."),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(ValueKeyArrayField("headers"))


class ManifestOauthForm(forms.Form):
    oauth = forms.JSONField(
        initial=list, help_text=_("OAuth settings"), required=False, label="OAuth"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class ManifestExistsForm(forms.Form):
    url = forms.URLField(
        max_length=255, help_text=_("The url it should check"), required=False
    )
    method = forms.ChoiceField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ),
        initial="GET",
        label=_("Request method"),
        required=False,
    )
    expected = forms.CharField(initial="", required=False)
    status_code = SimpleArrayField(
        forms.CharField(max_length=1000),
        required=False,
        initial=[],
        validators=[validate_status_code],
    )
    headers = forms.JSONField(
        initial=list,
        help_text=_("(optionally) This will overwrite the default headers."),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.initial = prepare_initial_data(self.initial)

        self.helper.layout = Layout(
            Div(
                Div(Field("method"), css_class="col-3"),
                Div(Field("url"), css_class="col-9"),
                css_class="row",
            ),
            Div(
                Field("expected"),
            ),
            Div(
                IntegerListField("status_code"),
            ),
            ValueKeyArrayField("headers"),
        )


class ManifestInitialDataForm(forms.Form):
    id = forms.CharField(
        max_length=100,
        help_text=_(
            "This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."
        ),
        validators=[validate_ID],
    )
    name = forms.CharField(
        max_length=255,
        help_text=_(
            "Type 'generate' if you want this value to be generated on the fly (different for each execution), will not need to be filled by a user"
        ),
    )
    description = forms.CharField(
        max_length=1255,
        help_text=_("This will be shown under the input field for extra context"),
        required=False,
    )
    secret = forms.BooleanField(
        initial=False,
        help_text="Enable this if the value should always be masked",
        required=False,
    )

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(Field("id"), css_class="col-9"),
                Div(Field("secret"), css_class="col-3"),
                css_class="row",
            ),
            Div(
                Field("name"),
            ),
            Div(
                Field("description"),
            ),
        )


class ManifestUserInfoForm(forms.Form):
    id = forms.CharField(
        max_length=100,
        help_text=_(
            "This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered."
        ),
        validators=[validate_ID],
    )
    name = forms.CharField(max_length=255)
    description = forms.CharField(
        max_length=1255,
        help_text=_("This will be shown under the input field for extra context"),
    )

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Field("id"),
            ),
            Div(
                Field("name"),
            ),
            Div(
                Field("description"),
            ),
        )


class ManifestExecuteForm(forms.Form):
    url = forms.URLField(
        max_length=255, help_text=_("The url it should trigger"), required=False
    )
    method = forms.ChoiceField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ),
        initial="GET",
        label=_("Request method"),
        required=False,
    )
    status_code = SimpleArrayField(
        forms.CharField(max_length=1000), required=False, initial=[]
    )
    cast_data_to_json = forms.BooleanField(
        initial=True,
        help_text=_(
            "Check this if the data should be send as json. When unchecked, it's send as a string."
        ),
        required=False,
    )
    headers = forms.JSONField(
        initial=list,
        help_text=_("(optionally) This will overwrite the default headers."),
        required=False,
    )
    data = forms.JSONField(initial=dict, required=False)
    store_data = forms.JSONField(
        initial=dict,
        help_text=_(
            "(optionally) if you want to store data that's the request returns, then you can do that here."
        ),
        required=False,
    )
    continue_if = forms.JSONField(
        initial=dict,
        help_text=_("(optionally) set up a condition to block any further requests"),
        required=False,
        validators=[validate_continue_if],
    )
    polling = forms.JSONField(
        initial=dict,
        help_text=_(
            "(optionally) rerun this request a specific amount of times until it passes"
        ),
        required=False,
        validators=[validate_polling],
    )
    save_as_file = forms.CharField(
        initial="",
        help_text=_(
            "(optionally) if this request returns a file, then you can save it to use later"
        ),
        required=False,
    )
    files = forms.JSONField(
        initial=dict,
        help_text=_(
            "(optionally) if you want to use any of the previous files to submit"
        ),
        required=False,
    )

    class Meta:
        fields = (
            "url",
            "method",
            "data",
            "headers",
            "store_data",
            "continue_if",
            "polling",
            "save_as_file",
            "files",
        )

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.initial = prepare_initial_data(self.initial)

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(Field("method"), css_class="col-3"),
                    Div(Field("url"), css_class="col-9"),
                    css_class="row",
                ),
                Div(Field("data")),
                Div(Field("cast_data_to_json")),
                Div(Field("store_data")),
                Div(Field("continue_if")),
                Div(Field("polling")),
                Div(Field("save_as_file")),
                Div(Field("files")),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
            )
        )
