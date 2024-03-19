from .models import ManifestExecute
from admin.integrations.models import ManifestForm
import json

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from admin.integrations.models import Integration, Manifest, ManifestExists, ManifestInitialData, ManifestExtraUserInfo, ManifestRevoke
from admin.integrations.utils import get_value_from_notation
from admin.sequences.models import IntegrationConfig
from admin.templates.forms import FieldWithExtraContext

class ValueKeyArrayField(FieldWithExtraContext):
    template = "value_key_array_field.html"

class IntegerListField(FieldWithExtraContext):
    template = "integer_list_field.html"

class ManifestFormForm(forms.ModelForm):
    class Meta:
        model = ManifestForm
        fields = ("id", "name", "type", "items", "options_source", "url", "method", "data", "headers", "data_from", "choice_value", "choice_name")

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        show_manual_items = "d-none"
        show_fetch_url = ""
        show_choice_options = ""
        if (
            self.instance is not None
            and self.instance.options_source == ManifestForm.OptionsSource.FIXED_LIST
        ):
            show_manual_items = ""
            show_fetch_url = "d-none"

        if (
            self.instance is not None
            and self.instance.type == ManifestForm.ItemsType.INPUT
        ):
            show_choice_options = "d-none"

        self.helper.layout = Layout(
            Div(
                Div(
                    Field("id"),
                    css_class="col-6"
                ),
                Div(
                    Field("name"),
                    css_class="col-6"
                ),
                css_class="row"
            ),
            Div(
                Div(
                    Field("type"),
                    css_class="col-6"
                ),
                Div(
                    Field("options_source"),
                    css_class=f"col-6 {show_choice_options}"
                ),
                css_class="row"
            ),
            Div(
                ValueKeyArrayField("items", extra_context={"disabled": disabled}),
                css_class=f"manual_items {show_manual_items} {show_choice_options}"
            ),
            Div(
                Div(
                    Div(
                        Field("method"),
                        css_class="col-3"
                    ),
                    Div(
                        Field("url"),
                        css_class="col-9"
                    ),
                    css_class="row"
                ),
                Div(
                    Field("data_from")
                ),
                Div(
                    Field("data")
                ),
                Div(
                    Div(
                        Field("choice_value"),
                        css_class="col-6"
                    ),
                    Div(
                        Field("choice_name"),
                        css_class="col-6"
                    ),
                    css_class="row"
                ),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
                css_class=f"fetch_items {show_fetch_url} {show_choice_options}"
            )
        )


class ManifestRevokeForm(forms.ModelForm):
    class Meta:
        model = ManifestRevoke
        fields = ("url", "method", "expected", "data", "headers", "expected", "status_code")

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Field("method"),
                        css_class="col-3"
                    ),
                    Div(
                        Field("url"),
                        css_class="col-9"
                    ),
                    css_class="row"
                ),
                Div(
                    Field("data")
                ),
                Div(
                    Field("expected")
                ),
                IntegerListField("status_code", extra_context={"disabled": disabled}),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
            )
        )

class ManifestHeadersForm(forms.ModelForm):
    class Meta:
        model = Manifest
        fields = ("headers",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            ValueKeyArrayField("headers")
        )

class ManifestExistsForm(forms.ModelForm):
    class Meta:
        model = ManifestExists
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    Field("method"),
                    css_class="col-3"
                ),
                Div(
                    Field("url"),
                    css_class="col-9"
                ),
                css_class="row"
            ),
            Div(
                Field("expected"),
            ),
            Div(
                IntegerListField("status_code"),
            ),
            ValueKeyArrayField("headers")
        )

class ManifestInitialDataForm(forms.ModelForm):
    class Meta:
        model = ManifestInitialData
        fields = ("id", "name", "secret", "description")

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Field("id"),
                    css_class="col-9"
                ),
                Div(
                    Field("secret"),
                    css_class="col-3"
                ),
                css_class="row"
            ),
            Div(
                Field("name"),
            ),
            Div(
                Field("description"),
            )
        )

class ManifestUserInfoForm(forms.ModelForm):
    class Meta:
        model = ManifestExtraUserInfo
        fields = ("id", "name", "description")

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
            )
        )


class ManifestExecuteForm(forms.ModelForm):
    class Meta:
        model = ManifestExecute
        fields = ("url", "method", "data", "headers", "store_data", "continue_if", "polling", "save_as_file", "files")

    def __init__(self, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Field("method"),
                        css_class="col-3"
                    ),
                    Div(
                        Field("url"),
                        css_class="col-9"
                    ),
                    css_class="row"
                ),
                Div(
                    Field("data")
                ),
                Div(
                    Field("store_data")
                ),
                Div(
                    Field("continue_if")
                ),
                Div(
                    Field("polling")
                ),
                Div(
                    Field("save_as_file")
                ),
                Div(
                    Field("files")
                ),
                ValueKeyArrayField("headers", extra_context={"disabled": disabled}),
            )
        )
