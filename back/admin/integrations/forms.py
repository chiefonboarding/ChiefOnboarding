from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms

from .asana import Asana
from .google import Google
from .slack import Slack


class AddGoogleUserForm(forms.Form):
    pass


class AddAsanaUserForm(forms.Form):
    teams = forms.MultipleChoiceField(
        label="Teams you want to add this new hire to",
        widget=forms.CheckboxSelectMultiple,
        choices=[(x["id"], x["name"]) for x in Asana().get_teams()],
    )


class AddSlackUserForm(forms.Form):
    pass
