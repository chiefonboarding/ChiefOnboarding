from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.utils.translation import ugettext_lazy as _

from users.models import User

from .models import AdminTask, AdminTaskComment


class AdminTaskCommentForm(forms.ModelForm):
    class Meta:
        model = AdminTaskComment
        fields = [
            "content",
        ]
        labels = {
            "content": _("Content")
        }


class AdminTaskUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance is not None and instance.completed:
            for field in self.fields:
                self.fields[field].widget.attrs["disabled"] = True

    class Meta:
        model = AdminTask
        fields = ["name", "assigned_to", "date", "priority"]
        labels = {
            "name": _("Name"),
            "assigned_to": _("Assigned to"),
            "date": _("Date"),
            "priority": _("Priority"),
        }


class AdminTaskCreateForm(forms.ModelForm):
    comment = forms.CharField(max_length=12500)
    new_hire = forms.ModelChoiceField(queryset=User.new_hires.all())
    assigned_to = forms.ModelChoiceField(queryset=User.admins.all())
    slack_user = forms.ModelChoiceField(
        queryset=User.objects.exclude(slack_user_id=""), to_field_name="slack_user_id"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option"].initial = 0

    class Meta:
        model = AdminTask
        fields = [
            "name",
            "new_hire",
            "assigned_to",
            "date",
            "priority",
            "comment",
            "option",
            "slack_user",
            "email",
        ]
        labels = {
            "name": _("Name"),
            "new_hire": _("New hire"),
            "assigned_to": _("Assigned to"),
            "date": _("Date"),
            "priority": _("Priority"),
            "comment": _("Comment"),
            "slack_user": _("Slack user"),
            "email": _("Email"),
            "option": _("Send email or text to extra user?"),
        }
