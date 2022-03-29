from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import (
    FieldWithExtraContext,
    ModelChoiceFieldWithCreate,
    MultiSelectField,
    TagModelForm,
)

from .models import Category, Resource
from .serializers import ChapterSerializer


class ChapterField(FieldWithExtraContext):
    template = "chapter_field.html"


class ResourceForm(TagModelForm):
    category = ModelChoiceFieldWithCreate(
        label=_("Category"),
        queryset=Category.objects.all(),
        to_field_name="name",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.fields["chapters"] = forms.JSONField()
        self.helper = FormHelper()
        none_class = ""
        if self.instance is None or not self.instance.course:
            none_class = " d-none"

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
                    HTML(
                        "<small style='top: -11px; position: relative;'>"
                        + _(
                            "Do not use only numbers as a category. Always add some "
                            "text."
                        )
                        + "</small>"
                    ),
                    css_class="col-6",
                ),
                Div(
                    Field("course"),
                    css_class="col-2",
                ),
                Div(
                    Field("on_day"),
                    css_class="col-2" + none_class,
                ),
                Div(
                    Field("remove_on_complete"),
                    css_class="col-2" + none_class,
                ),
                css_class="row",
            ),
            Div(
                Div(
                    ChapterField(
                        "chapters",
                        extra_context={
                            "chapters": ChapterSerializer(
                                self.instance.chapters.filter(
                                    parent_chapter__isnull=True
                                ),
                                many=True,
                            ).data
                        },
                    ),
                    css_class="col-12",
                ),
            ),
        )

    class Meta:
        model = Resource
        fields = ("name", "tags", "category", "course", "on_day", "remove_on_complete")
        help_texts = {
            "course": _("When enabled, new hires will have to walk through this"),
            "remove_on_complete": _(
                "If disabled, it will turn into a normal resource after completing"
            ),
        }
