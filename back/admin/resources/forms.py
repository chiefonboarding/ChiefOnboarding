from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout
from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from admin.templates.forms import (
    FieldWithExtraContext,
    ModelChoiceFieldWithCreate,
    MultiSelectField,
    TagModelForm,
)
from misc.mixins import FilterDepartmentsFieldByUserMixin

from .models import Category, Chapter, Resource
from .serializers import ChapterSerializer


class ChapterField(FieldWithExtraContext):
    template = "chapter_field.html"


class ResourceForm(FilterDepartmentsFieldByUserMixin, TagModelForm):
    category = ModelChoiceFieldWithCreate(
        label=_("Category"),
        queryset=Category.objects.all(),
        to_field_name="name",
        required=False,
    )
    counter = 0

    def _create_or_update_chapter(self, resource, parent, chapter):
        if isinstance(chapter["id"], int):
            chap = Chapter.objects.get(id=chapter["id"])
            chap.name = chapter["name"]
            chap.content = chapter["content"]
            chap.resource = resource
            chap.order = self.counter
            chap.save()
        else:
            chap = Chapter.objects.create(
                resource=resource,
                name=chapter["name"],
                content=chapter["content"],
                type=chapter["type"],
                order=self.counter,
            )
            if parent is not None:
                chap.parent_chapter = Chapter.objects.get(id=parent)
                chap.save()
        self.counter += 1

        # Return new/updated item id
        return chap.id

    def _get_child_chapters(self, resource, parent, children):
        if len(children) == 0:
            return

        for chapter in children:
            # Save or update item
            parent_id = self._create_or_update_chapter(resource, parent, chapter)

            # Go one level deeper - check and create chapters
            self._get_child_chapters(resource, parent_id, chapter["children"])

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.fields["chapters"] = forms.JSONField()
        self.helper = FormHelper()
        self.helper.form_tag = False
        none_class = "d-none"
        if (self.instance is not None and self.instance.course) or (
            "course" in self.data and self.data["course"] == "on"
        ):
            none_class = ""

        if self.instance.pk is None:
            chapters = []
        else:
            chapters = ChapterSerializer(
                self.instance.chapters.filter(parent_chapter__isnull=True),
                many=True,
            ).data

        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    css_class="col-6",
                ),
                Div(
                    MultiSelectField("departments"),
                    css_class="col-3",
                ),
                Div(
                    MultiSelectField("tags"),
                    css_class="col-3",
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
                    css_class="col-2 " + none_class,
                ),
                Div(
                    Field("remove_on_complete"),
                    css_class="col-2 " + none_class,
                ),
                css_class="row",
            ),
            Div(
                Div(
                    ChapterField(
                        "chapters",
                        extra_context={"chapters": chapters},
                    ),
                    css_class="col-12",
                ),
            ),
        )

    class Meta:
        model = Resource
        fields = (
            "name",
            "tags",
            "category",
            "course",
            "on_day",
            "remove_on_complete",
            "departments",
        )
        help_texts = {
            "course": _("When enabled, new hires will have to walk through this"),
            "remove_on_complete": _(
                "If disabled, it will turn into a normal resource after completing"
            ),
        }

    @transaction.atomic
    def save(self, commit=True):
        chapters = self.cleaned_data.pop("chapters", [])
        instance = super(ResourceForm, self).save(commit=commit)

        Chapter.objects.filter(resource=instance).update(resource=None)
        # Root chapters
        for chapter in chapters:
            parent_id = self._create_or_update_chapter(instance, None, chapter)

            self._get_child_chapters(instance, parent_id, chapter["children"])
        return instance
