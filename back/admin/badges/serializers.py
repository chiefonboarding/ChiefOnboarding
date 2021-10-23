from rest_framework import serializers

from misc.fields import ContentField
from misc.models import File
from misc.serializers import FileSerializer

from .models import Badge


class BadgeSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default="badge", read_only=True)
    content = ContentField()
    image = FileSerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        source="image", queryset=File.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Badge
        fields = "__all__"
