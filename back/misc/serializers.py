from django.conf import settings
from rest_framework import serializers

from .models import File
from .s3 import S3


class FileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = "__all__"

    def get_file_url(self, obj):
        if settings.AWS_STORAGE_BUCKET_NAME == "" or obj.key == "":
            return ""
        return S3().get_file(obj.key)
