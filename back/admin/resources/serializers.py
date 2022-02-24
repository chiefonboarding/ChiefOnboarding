from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from .fields import CategoryField
from .models import Category, Chapter, Resource


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ChapterSerializer(serializers.HyperlinkedModelSerializer):
    children = SerializerMethodField()

    class Meta:
        model = Chapter
        fields = ("id", "name", "content", "type", "children", "order")

    def get_children(self, obj):
        return ChapterSerializer(
            Chapter.objects.filter(parent_chapter=obj).order_by("order"), many=True
        ).data


class ResourceSerializer(serializers.HyperlinkedModelSerializer):
    search_type = serializers.CharField(default="resource", read_only=True)
    id = serializers.IntegerField(required=False)
    category = CategoryField(allow_null=True)

    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = (
            "id",
            "name",
            "category",
            "course",
            "search_type",
            "on_day",
            "tags",
            "remove_on_complete",
            "chapters",
        )


class ResourceCourseSerializer(ResourceSerializer):

    class Meta:
        model = Resource
        fields = (
            "id",
            "name",
            "category",
            "course",
            "on_day",
            "tags",
            "remove_on_complete",
            "chapters",
        )
