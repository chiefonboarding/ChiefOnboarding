from django.contrib.auth import get_user_model
from rest_framework import serializers

from misc.serializers import FileSerializer

from .models import Introduction


class IntroEmployeeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    profile_image = FileSerializer(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "position",
            "phone",
            "full_name",
            "slack_user_id",
            "twitter",
            "facebook",
            "linkedin",
            "message",
            "profile_image",
            "name",
        )

    def get_name(self, obj):
        return obj.first_name + " " + obj.last_name


class IntroductionSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default="introduction", read_only=True)
    id = serializers.IntegerField(required=False)
    intro_person = IntroEmployeeSerializer(read_only=True)
    intro_person_id = serializers.PrimaryKeyRelatedField(source="intro_person", queryset=get_user_model().objects.all())

    class Meta:
        model = Introduction
        fields = "__all__"
