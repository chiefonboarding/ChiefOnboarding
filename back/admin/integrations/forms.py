from django import forms
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper

from .asana import Asana
from .google import Google
from .slack import Slack


class AddGoogleUserForm(forms.Form):
    pass


class AddAsanaUserForm(forms.Form):
    teams = forms.MultipleChoiceField(
        label=_("Teams you want to add this new hire to"),
        widget=forms.CheckboxSelectMultiple,
        choices=[(x["id"], x["name"]) for x in Asana().get_teams()],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class AddSlackUserForm(forms.Form):
    pass
