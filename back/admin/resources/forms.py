from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from crispy_forms.utils import TEMPLATE_PACK
from django import forms

from admin.templates.forms import MultiSelectField, WYSIWYGField, FieldWithExtraContext
from organization.models import Tag

from .models import Resource, Category
from .serializers import ChapterSerializer
from admin.templates.forms import ModelChoiceFieldWithCreate


class ChapterField(FieldWithExtraContext):
    template = "chapter_field.html"


class ResourceForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), to_field_name="name"
    )
    category = ModelChoiceFieldWithCreate(
        queryset=Category.objects.all(), to_field_name="name", required=False
    )

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.fields['chapters'] = forms.JSONField()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    css_class="col-6",
                ),
                Div(
                    MultiSelectField("tags"),
                    css_class="col-6",
                ),
                css_class="row",
            ),
            Div(
                Div(
                    Field("category", css_class="add"),
                    css_class="col-6",
                ),
                Div(
                    Field("course"),
                    css_class="col-2",
                ),
                Div(
                    Field("on_day"),
                    css_class="col-2 d-none",
                ),
                Div(
                    Field("remove_on_complete"),
                    css_class="col-2 d-none",
                ),
                css_class="row",
            ),
            Div(
                Div(ChapterField("chapters", extra_context={"chapters": ChapterSerializer(self.instance.chapters.filter(parent_chapter__isnull=True), many=True).data}), css_class="col-12"),
            ),
        )

    class Meta:
        model = Resource
        fields = ("name", "tags", "category", "course", "on_day", "remove_on_complete")
        labels = {
            'course': 'Is a course item',
            'on_day': 'Workday that this item is due',
            'remove_on_complete': 'Remove item when new hire walked through'
        }
        help_texts = {
            'course': 'When enabled, new hires will have to walk through this',
            'remove_on_complete': 'If disabled, it will turn into a normal resource after completing'
        }

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        return [tag.name for tag in tags]
