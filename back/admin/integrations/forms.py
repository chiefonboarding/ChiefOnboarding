from django import forms
from django.utils.translation import ugettext_lazy as _

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
    )


class AddSlackUserForm(forms.Form):
    pass
