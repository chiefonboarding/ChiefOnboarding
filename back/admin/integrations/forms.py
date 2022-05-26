import json

import requests
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError

from .models import Integration
from .serializers import ManifestSerializer


class IntegrationConfigForm(forms.ModelForm):
    def _get_result(self, notation, value):
        # if we don't need to go into props, then just return the value
        if notation == "":
            return value

        notations = notation.split(".")
        for notation in notations:
            value = value[notation]
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        integration = Integration.objects.get(id=self.instance.id)
        form = self.instance.manifest["form"]
        self.helper = FormHelper()
        self.helper.form_tag = False
        for item in form:
            if item["type"] in ["multiple_choice", "choice"]:

                if item["type"] == "multiple_choice":
                    form_field = forms.MultipleChoiceField
                else:
                    form_field = forms.ChoiceField

                # If there is a url to fetch the items from then do so
                if "url" in item:
                    option_data = requests.get(
                        integration._replace_vars(item["url"]),
                        headers=integration._headers,
                    ).json()
                else:
                    # No url, so get the static items
                    option_data = item["items"]

                self.fields[item["id"]] = form_field(
                    label=item["name"],
                    widget=forms.CheckboxSelectMultiple
                    if item["type"] == "multiple_choice"
                    else forms.Select,
                    choices=[
                        (
                            self._get_result(item.get("choice_id", "id"), x),
                            self._get_result(item.get("choice_name", "name"), x),
                        )
                        for x in self._get_result(
                            item.get("data_from", ""), option_data
                        )
                    ],
                    required=False,
                )

    class Meta:
        model = Integration
        fields = ()


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ("name", "manifest")

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
            if "type" in item and item["type"] == "generated":
                self.fields[item["id"]].widget = forms.HiddenInput()

    def save(self):
        integration = self.instance
        integration.extra_args = self.cleaned_data
        integration.save()
        return integration

    class Meta:
        model = Integration
        fields = ()
