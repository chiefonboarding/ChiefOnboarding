from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from misc.serializers import ContentCourseSerializer

from .fields import CategoryField
from .models import Category, Chapter, CourseAnswer, Resource


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
        return ChapterSerializer(Chapter.objects.filter(parent_chapter=obj).order_by("order"), many=True).data


class ChapterCourseSerializer(ChapterSerializer):
    content = ContentCourseSerializer(many=True)

    class Meta:
        model = Chapter
        fields = ("id", "name", "content", "type", "parent_chapter")


class CourseAnswerSerializer(serializers.ModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CourseAnswer
        fields = "__all__"


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
    chapters = ChapterCourseSerializer(many=True, read_only=True)

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


class ResourceSlimSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Resource
        fields = ("id", "name")
