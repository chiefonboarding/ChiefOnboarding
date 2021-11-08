from django.conf import settings
from rest_framework import serializers

from .models import Content, File
from .s3 import S3


class FileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = "__all__"

    def get_file_url(self, obj):
        if settings.AWS_STORAGE_BUCKET_NAME == "":
            return ""
        return S3().get_file(obj.key)


class ContentSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, required=False)
    type = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = "__all__"

    def get_type(self, obj):
        return obj.get_type_display()

    def get_image_url(self, obj):
        if obj.type == "image" and obj.files.exists() and settings.AWS_STORAGE_BUCKET_NAME != "":
            return obj.files.first().get_url()
        return ""


class ContentCourseSerializer(ContentSerializer):
    class Meta:
        model = Content
        fields = ("files", "type", "image_url", "items", "content")


class ContentPostSerializer(serializers.ModelSerializer):
    # serializer used for fields.py to post data to
    content = serializers.CharField(required=False, allow_blank=True)
    files = FileSerializer(many=True, required=False)

    class Meta:
        model = Content
        fields = "__all__"
