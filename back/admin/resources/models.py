from django.db import models
from django.db.models import Prefetch

from misc.models import Content
from organization.models import BaseItem


class FullManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "chapters",
                    queryset=Chapter.objects.select_related("parent_chapter").prefetch_related("content__files"),
                )
            )
            .order_by("name")
        )


class FullTemplateManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "chapters",
                    queryset=Chapter.objects.select_related("parent_chapter").prefetch_related("content__files"),
                )
            )
            .filter(template=True)
            .order_by("name")
        )


class Category(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Resource(BaseItem):
    category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True)

    # course part
    course = models.BooleanField(default=False)
    on_day = models.IntegerField(default=0)
    remove_on_complete = models.BooleanField(default=False)

    objects = FullManager()
    templates = FullTemplateManager()

    def next_chapter(self, current_id, course):
        chapters = self.chapters.exclude(type=1)
        if not course:
            chapters = self.chapters.filter(type=0)

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


class Chapter(models.Model):
    CHAPTER_TYPE = ((0, "page"), (1, "folder"), (2, "questions"))
    parent_chapter = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="chapters", null=True)
    name = models.CharField(max_length=240)
    content = models.ManyToManyField(Content)
    type = models.IntegerField(choices=CHAPTER_TYPE)

    def slack_menu_item(self):
        name = self.name
        if len(name) > 75:
            name = name[:70] + "..."
        if self.parent_chapter is not None:
            name = "- " + name
        return {
            "text": {"type": "plain_text", "text": name, "emoji": True},
            "value": str(self.id),
        }


class CourseAnswer(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    answers = models.JSONField(models.TextField(default="[]"), default=list)
