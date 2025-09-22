from django import forms
from django.utils.translation import gettext_lazy as _

from users.selectors import (
    get_all_managers_and_admins_for_departments_of_user, 
    get_all_managers_and_admins_for_departments_of_user_with_slack, 
    get_all_new_hires_for_departments_of_user
)

from .models import AdminTask, AdminTaskComment


class AdminTaskCommentForm(forms.ModelForm):
    class Meta:
        model = AdminTaskComment
        fields = [
            "content",
        ]



class AdminTaskCreateForm(forms.ModelForm):
    comment = forms.CharField(label=_("Comment"), max_length=12500)
    date = forms.DateField(
        label=_("Date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format=("%Y-%m-%d")),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if "option" in self.fields:
            self.fields["option"].initial = 0
        if "new_hire" in self.fields:
            self.fields["new_hire"].queryset = get_all_new_hires_for_departments_of_user(user=user)
        self.fields["assigned_to"].queryset = get_all_managers_and_admins_for_departments_of_user(user=user)
        if "slack_user" in self.fields:
            self.fields["slack_user"].queryset = get_all_managers_and_admins_for_departments_of_user_with_slack(user=user)

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

class AdminTaskUpdateForm(AdminTaskCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance is not None and instance.completed:
            for field in self.fields:
                self.fields[field].widget.attrs["disabled"] = True

    class Meta:
        model = AdminTask
        fields = ["name", "assigned_to", "date", "priority"]

