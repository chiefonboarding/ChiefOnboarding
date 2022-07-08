from django import forms


class QuestionsForm(forms.Form):
    def __init__(self, items, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for idx, question in enumerate(items):
            self.fields[f"item-{idx}"] = forms.ChoiceField(
                choices=(
                    (option["id"], option["text"]) for option in question["items"]
                ),
                widget=forms.RadioSelect,
                label=question["content"],
            )
