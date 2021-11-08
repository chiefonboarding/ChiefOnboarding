from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.serializers import AdminSerializer, NewHireSerializer

from .models import AdminTask, AdminTaskComment


class CommentSerializer(serializers.ModelSerializer):
    comment_by = AdminSerializer(read_only=True)

    class Meta:
        model = AdminTaskComment
        fields = ("id", "content", "date", "comment_by")
        ordering = ("-id",)


class CommentPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AdminTaskComment
        fields = ("content",)


class AdminTaskSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    date = serializers.DateField(required=False)

    new_hire = NewHireSerializer(read_only=True)
    new_hire_id = serializers.PrimaryKeyRelatedField(source="new_hire", queryset=get_user_model().objects.all())
    assigned_to = AdminSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(source="assigned_to", queryset=get_user_model().objects.all())

    def get_comments(self, instance):
        try:
            comments = instance.comment.all().order_by("-id")
        except:
            return []
        return CommentSerializer(comments, many=True, read_only=True).data

    def validate(self, value):
        if value["option"] == 2 and (value["slack_user"] == "" or value["slack_user"] is None):
            raise serializers.ValidationError("Please select a user to send a message to.")
        if value["option"] == 1 and (value["email"] == "" or value["email"] is None):
            raise serializers.ValidationError("Please enter an email address.")
        return value

    class Meta:
        model = AdminTask
        fields = "__all__"
