from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from misc.fields import ContentJSONField
from misc.mixins import ContentMixin
from organization.models import BaseItem, Notification


class Category(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class ResourceManager(models.Manager):
    def search(self, u, query):
        query = SearchQuery(query)
        vector = (
            SearchVector("name", weight="A")
            + SearchVector("chapters__content", weight="B")
            + SearchVector("chapters__name", weight="A")
        )
        results = (
            super()
            .get_queryset()
            .annotate(
                rank=SearchRank(vector, query),
                headline=SearchHeadline(
                    "name",
                    query,
                    fragment_delimiter="...",
                ),
                inner=SearchHeadline(
                    "chapters__content",
                    query,
                    fragment_delimiter="...",
                ),
            )
            .filter(rank__gte=0.3, resource_new_hire__user=u)
            .order_by("rank")
            .values_list("pk", flat=True)
        )
        return super().get_queryset().filter(pk__in=results)


class Resource(BaseItem):
    category = models.ForeignKey(
        "Category", verbose_name=_("Category"), on_delete=models.CASCADE, null=True
    )

    # course part
    course = models.BooleanField(verbose_name=_("Is a course item"), default=False)
    on_day = models.IntegerField(
        verbose_name=_("Workday that this item is due"), default=1
    )
    remove_on_complete = models.BooleanField(
        verbose_name=_("Remove item when new hire walked through"), default=False
    )

    objects = ResourceManager()

    def get_icon_template(self):
        return render_to_string("_resource_icon.html")

    @property
    def notification_add_type(self):
        return Notification.Type.ADDED_RESOURCE

    def duplicate(self, change_name=True):
        old_resource = Resource.objects.get(pk=self.pk)
        self.pk = None
        if change_name:
            self.name = _("%(name)s (duplicate)") % {"name": self.name}
        self.save()

        # old vs new ids for referencing parent_chapters
        chapter_ids = []

        for chapter in old_resource.chapters.all().order_by("parent_chapter"):
            new_chapter = chapter.duplicate()
            new_chapter.resource = self
            new_chapter.save()
            if new_chapter.parent_chapter is not None:
                new_parent_chapter = next(
                    (
                        x["new"]
                        for x in chapter_ids
                        if x["old"] == chapter.parent_chapter.id
                    ),
                    None,
                )
                new_chapter.parent_chapter = new_parent_chapter
                new_chapter.save()

            chapter_ids.append({"old": chapter.id, "new": new_chapter.id})

        return self

    @property
    def update_url(self):
        return reverse("resources:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("resources:delete", args=[self.id])

    def chapters_display(self):
        return self.chapters.all().filter(parent_chapter__isnull=True)

    @property
    def first_chapter_id(self):
        return self.chapters.all()[0].id

    def next_chapter(self, current_id, course):
        # We can't fetch course from the object, as the user might have already
        # passed it and it now should show as normal resource for them
        # Only used for Slack
        chapters = self.chapters.exclude(type=Chapter.Type.FOLDER)
        if not course:
            chapters = self.chapters.filter(type=Chapter.Type.PAGE)

        chapter = chapters.first()

        if current_id == -1:
            return chapter
        for index, item in enumerate(chapters):
            if item.id == int(current_id):
                if len(chapters) == index + 1:
                    return None
                chapter = chapters[index + 1]
                break
        return chapter


class Chapter(ContentMixin, models.Model):
    class Type(models.IntegerChoices):
        PAGE = 0, _("Page")
        FOLDER = 1, _("Folder")
        QUESTIONS = 2, _("Questions")

    parent_chapter = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="chapters", null=True
    )
    name = models.CharField(max_length=240)
    content = ContentJSONField(default=dict)
    type = models.IntegerField(choices=Type.choices)
    order = models.IntegerField(default=0)

    def duplicate(self):
        self.pk = None
        self.save()
        return self

    def children(self):
        return Chapter.objects.filter(parent_chapter__id=self.id).order_by("order")

    def slack_menu_item(self):
        # Small top menu in the dialog

        # Slack's max length for the name is 75 chars
        name = self.name if len(self.name) < 75 else self.name[:69] + "..."

        # If it's within another item, then add a - to indicate that
        if self.parent_chapter is not None:
            name = "- " + name

        return {
            "text": {"type": "plain_text", "text": name, "emoji": True},
            "value": str(self.id),
        }

    class Meta:
        ordering = ("order", "pk")


class CourseAnswer(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    answers = models.JSONField(default=list)
