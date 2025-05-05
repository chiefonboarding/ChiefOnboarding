from django import forms
import os


class FileExtensionValidator:
    def __init__(self, allowed_extensions):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def __call__(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.allowed_extensions:
            raise forms.ValidationError(
                f"File type not supported. Allowed types: {', '.join(self.allowed_extensions)}"
            )


class FileSizeValidator:
    def __init__(self, max_size_mb):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def __call__(self, value):
        if value.size > self.max_size_bytes:
            raise forms.ValidationError(
                f"File too large. Maximum size is {self.max_size_bytes / (1024 * 1024):.1f} MB."
            )


class QuestionsForm(forms.Form):
    def __init__(self, items, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for idx, question in enumerate(items):
            question_type = question.get('question_type', 'multiple_choice')

            if question_type == 'multiple_choice' or not question_type:
                self.fields[f"item-{idx}"] = forms.ChoiceField(
                    choices=(
                        (option["id"], option["text"]) for option in question["items"]
                    ),
                    widget=forms.RadioSelect,
                    label=question["content"],
                )
            elif question_type == 'file_upload':
                allowed_extensions = question.get('allowed_extensions', '.pdf,.doc,.docx,.txt')
                allowed_ext_list = allowed_extensions.split(',')
                help_text = f"Allowed file types: {allowed_extensions}"
                max_size = question.get('max_file_size', 5)
                required = question.get('required', True)

                if max_size:
                    help_text += f" (Max size: {max_size}MB)"

                field = forms.FileField(
                    label=question["content"],
                    help_text=help_text,
                    required=required,
                    validators=[
                        FileExtensionValidator(allowed_ext_list),
                        FileSizeValidator(max_size)
                    ]
                )

                self.fields[f"item-{idx}"] = field

            elif question_type == 'photo_upload':
                allowed_extensions = question.get('allowed_extensions', '.jpg,.jpeg,.png,.gif')
                allowed_ext_list = allowed_extensions.split(',')
                help_text = f"Allowed image formats: {allowed_extensions}"
                max_size = question.get('max_file_size', 5)
                required = question.get('required', True)

                if max_size:
                    help_text += f" (Max size: {max_size}MB)"

                field = forms.ImageField(
                    label=question["content"],
                    help_text=help_text,
                    required=required,
                    validators=[
                        FileExtensionValidator(allowed_ext_list),
                        FileSizeValidator(max_size)
                    ]
                )

                self.fields[f"item-{idx}"] = field

            elif question_type == 'fill_in_blank':
                placeholder = question.get('placeholder', 'Fill in your answer')

                # Process the question content to show where the blank is
                content = question["content"]
                # Replace XXXX or [blank] with an underline to indicate the blank
                content = content.replace('XXXX', '________').replace('[blank]', '________')

                self.fields[f"item-{idx}"] = forms.CharField(
                    label=content,
                    widget=forms.TextInput(attrs={
                        'placeholder': placeholder,
                        'class': 'form-control fill-in-blank-input'
                    }),
                    required=True,
                )
            elif question_type == 'free_text':
                min_length = question.get('min_length', 0)
                max_length = question.get('max_length', 1000)
                placeholder = question.get('placeholder', 'Enter your answer here...')

                self.fields[f"item-{idx}"] = forms.CharField(
                    label=question["content"],
                    widget=forms.Textarea(attrs={
                        'placeholder': placeholder,
                        'rows': 4,
                        'class': 'form-control'
                    }),
                    min_length=min_length,
                    max_length=max_length,
                    required=True,
                )
            elif question_type == 'rating_scale':
                min_rating = int(question.get('min_rating', 1))
                max_rating = int(question.get('max_rating', 5))
                step = float(question.get('step', 1))

                # Create choices for the rating scale
                choices = [(str(i), str(i)) for i in range(min_rating, max_rating + 1, int(step) if step >= 1 else 1)]

                # Add labels if enabled
                show_labels = question.get('show_labels', True)
                help_text = ""
                if show_labels:
                    min_label = question.get('min_label', 'Poor')
                    max_label = question.get('max_label', 'Excellent')
                    help_text = f"{min_label} (1) to {max_label} ({max_rating})"

                self.fields[f"item-{idx}"] = forms.ChoiceField(
                    label=question["content"],
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'rating-scale'}),
                    help_text=help_text,
                    required=True,
                )
            elif question_type == 'date_picker':
                min_date = question.get('min_date', '')
                max_date = question.get('max_date', '')
                required = question.get('required', True)
                placeholder = question.get('placeholder', 'Select a date')

                attrs = {'placeholder': placeholder, 'class': 'form-control'}
                if min_date:
                    attrs['min'] = min_date
                if max_date:
                    attrs['max'] = max_date

                self.fields[f"item-{idx}"] = forms.DateField(
                    label=question["content"],
                    widget=forms.DateInput(attrs=attrs, format='%Y-%m-%d', type='date'),
                    required=required,
                )
            elif question_type == 'checkbox_list':
                choices = [(option["id"], option["text"]) for option in question["items"]]
                min_selections = int(question.get('min_selections', 0))
                max_selections = int(question.get('max_selections', 0))

                help_text = ""
                if min_selections > 0 and max_selections > 0:
                    help_text = f"Select between {min_selections} and {max_selections} options"
                elif min_selections > 0:
                    help_text = f"Select at least {min_selections} options"
                elif max_selections > 0:
                    help_text = f"Select up to {max_selections} options"

                self.fields[f"item-{idx}"] = forms.MultipleChoiceField(
                    label=question["content"],
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,
                    help_text=help_text,
                    required=min_selections > 0,
                )
