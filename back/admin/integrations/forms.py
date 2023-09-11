import json

from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from admin.integrations.utils import get_value_from_notation

from .models import Integration
from .serializers import ManifestSerializer


class IntegrationConfigForm(forms.ModelForm):
    def _expected_example(self, form_item):
        def _add_items(form_item):
            items = []
            # Add two example items
            for item in range(2):
                items.append(
                    {
                        form_item.get("choice_value", "id"): item,
                        form_item.get("choice_name", "name"): f"name {item}",
                    }
                )
            return items

        inner = form_item.get("data_from", "")
        if inner == "":
            return _add_items(form_item)

        # This is pretty ugly, but we are building a json string first
        # and then convert it to a real json object to avoid nested loops
        notations = inner.split(".")
        stringified_json = "{"
        for idx, notation in enumerate(notations):
            stringified_json += f'"{notation}":'
            if idx + 1 == len(notations):
                stringified_json += json.dumps(_add_items(form_item))
                stringified_json += "}" * len(notations)
            else:
                stringified_json += "{"

        return json.loads(stringified_json)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        integration = Integration.objects.get(id=self.instance.id)
        form = self.instance.manifest["form"]
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.error = None
        for item in form:
            if item["type"] == "input":
                self.fields[item["id"]] = forms.CharField(
                    label=item["name"],
                    required=False,
                )

            if item["type"] in ["choice", "multiple_choice"]:
                # If there is a url to fetch the items from then do so
                if "url" in item:
                    success, response = integration.run_request(item)
                    if not success:
                        self.error = response
                        return

                    option_data = response.json()
                else:
                    # No url, so get the static items
                    option_data = item["items"]

                # Can we select one or multiple?
                if item["type"] == "choice":
                    field = forms.ChoiceField
                else:
                    field = forms.MultipleChoiceField

                try:
                    self.fields[item["id"]] = field(
                        label=item["name"],
                        widget=forms.CheckboxSelectMultiple
                        if item["type"] == "multiple_choice"
                        else forms.Select,
                        choices=[
                            (
                                get_value_from_notation(
                                    item.get("choice_value", "id"), x
                                ),
                                get_value_from_notation(
                                    item.get("choice_name", "name"), x
                                ),
                            )
                            for x in get_value_from_notation(
                                item.get("data_from", ""), option_data
                            )
                        ],
                        required=False,
                    )
                except Exception:
                    expected = self._expected_example(item)

                    self.error = (
                        f"Form item ({item['name']}) could not be rendered. Format "
                        "was different than expected.<br><h2>Expected format:"
                        f"</h2><pre>{json.dumps(expected, indent=4)}</pre><br><h2>"
                        "Got from server:</h2><pre>"
                        f"{json.dumps(option_data, indent=4)}</pre>"
                    )
                    break

    class Meta:
        model = Integration
        fields = ()


# Credits: https://stackoverflow.com/a/72256767
# Removed the sort options
class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, **kwargs):
        super().__init__(*args, indent=4, **kwargs)


class IntegrationForm(forms.ModelForm):
    manifest = forms.JSONField(encoder=PrettyJSONEncoder)

    class Meta:
        model = Integration
        fields = ("name", "manifest_type", "manifest")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manifest_type"].required = True

    def clean_manifest(self):
        manifest = self.cleaned_data["manifest"]
        manifest_serializer = ManifestSerializer(data=manifest)
        if not manifest_serializer.is_valid():
            raise ValidationError(json.dumps(manifest_serializer.errors))
        return manifest


class IntegrationExtraArgsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial_data = self.instance.extra_args
        for item in self.instance.manifest["initial_data_form"]:
            self.fields[item["id"]] = forms.CharField(
                label=item["name"], help_text=item["description"]
            )
            # Check if item was already saved - load data back in form
            if item["id"] in initial_data:
                self.fields[item["id"]].initial = initial_data[item["id"]]
            # If field is secret field, then hide it - values are generated on the fly
            if "name" in item and item["name"] == "generate":
                self.fields[item["id"]].required = False
                self.fields[item["id"]].widget = forms.HiddenInput()

    def save(self):
        integration = self.instance
        integration.extra_args = self.cleaned_data
        integration.save()
        return integration

    class Meta:
        model = Integration
        fields = ()


class IntegrationExtraUserInfoForm(forms.ModelForm):
    def __init__(self, missing_info=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if missing_info is None:
            missing_info = self.instance.missing_extra_info

        for item in missing_info:
            self.fields[item["id"]] = forms.CharField(
                label=item["name"], help_text=item["description"]
            )

    def save(self):
        user = self.instance
        user.extra_fields |= self.cleaned_data
        user.save()
        return user

    class Meta:
        model = get_user_model()
        fields = ()
