from django import forms

from .models import AdminTask, AdminTaskComment


class AdminTaskCommentForm(forms.ModelForm):
    class Meta:
        model = AdminTaskComment
        fields = [
            "content",
        ]


class AdminTaskUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance is not None and instance.completed:
            for field in self.fields:
                print(field)
                self.fields[field].widget.attrs["disabled"] = True

    class Meta:
        model = AdminTask
        fields = ["name", "assigned_to", "date", "priority"]
