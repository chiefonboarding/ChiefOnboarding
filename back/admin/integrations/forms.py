import requests
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Integration


class IntegrationConfigForm(forms.ModelForm):
    def _get_result(self, notation, value):
        notations = notation.split(".")
        for notation in notations:
            value = value[notation]
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        integration = Integration.objects.get(id=self.instance.id)
        form = self.instance.manifest['form']
        for item in form:
            if item["type"] == "multiple_choice":
                option_data = requests.get(integration._replace_vars(item["url"]), headers=integration._headers).json()
                self.fields[item["id"]] = forms.MultipleChoiceField(
                    label=item["name"],
                    widget=forms.CheckboxSelectMultiple,
                    choices=[
                        (
                            self._get_result(item["choice_id"], x),
                            self._get_result(item["choice_name"], x)
                        )
                        for x in self._get_result(item["items"], option_data)
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


class IntegrationExtraArgsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial_data = self.instance.extra_args
        for item in self.instance.manifest['initial_data_form']:
            self.fields[item["id"]] = forms.CharField(
                label=item["name"],
                help_text=item["description"]
            )
            if item["id"] in initial_data:
                self.fields[item["id"]].initial = initial_data[item["id"]]

    def save(self):
        integration = self.instance
        integration.extra_args = self.cleaned_data
        integration.save()
        return integration

    class Meta:
        model = Integration
        fields = ()
