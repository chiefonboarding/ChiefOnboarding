from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from .models import Chapter


class ChapterSerializer(serializers.HyperlinkedModelSerializer):
    children = SerializerMethodField()

    class Meta:
        model = Chapter
        fields = ("id", "name", "content", "type", "children", "order")

    def get_children(self, obj):
        return ChapterSerializer(
            Chapter.objects.filter(parent_chapter=obj).order_by("order"), many=True
        ).data
