from rest_framework import serializers

from admin.badges.models import Badge
from admin.preboarding.serializers import PreboardingSerializer
from admin.resources.models import Resource
from admin.resources.serializers import (ChapterSerializer,
                                         CourseAnswerSerializer,
                                         ResourceCourseSerializer,
                                         ResourceSerializer)
from admin.to_do.models import ToDo
from misc.fields import ContentField
from misc.s3 import S3
from users.models import PreboardingUser, ResourceUser, ToDoUser


class ToDoNewHireSerializer(serializers.ModelSerializer):
    content = ContentField()

    class Meta:
        model = ToDo
        fields = ("id", "name", "due_on_day", "form", "content")


class ToDoUserSerializer(serializers.ModelSerializer):
    to_do = ToDoNewHireSerializer(read_only=True)
    completed_form = serializers.SerializerMethodField()

    class Meta:
        model = ToDoUser
        fields = ("id", "to_do", "completed", "reminded", "completed_form")

    def get_completed_form(self, obj):
        return len(obj.form) > 0


class PreboardingUserSerializer(serializers.ModelSerializer):
    preboarding = PreboardingSerializer(read_only=True)

    class Meta:
        model = PreboardingUser
        fields = ("id", "preboarding", "form", "completed", "order")


class NewHireResourceSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    item = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ("id", "name", "category", "course", "item")

    def get_item(self, obj):
        if obj.chapters.count() == 1:
            return ChapterSerializer(obj.chapters.all()[0]).data


class NewHireResourceItemSerializer(serializers.ModelSerializer):
    resource = ResourceCourseSerializer(read_only=True)
    answers = CourseAnswerSerializer(read_only=True, many=True)

    class Meta:
        model = ResourceUser
        fields = ("id", "resource", "step", "answers")


class NewHireBadgeSerializer(serializers.ModelSerializer):
    content = ContentField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ("content", "image", "name")

    def get_image(self, obj):
        if obj.image is not None:
            return S3().get_file(obj.image.key)
        return ""
