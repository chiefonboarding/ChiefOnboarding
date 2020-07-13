from rest_framework import serializers
from .models import Badge
from misc.serializers import FileSerializer

from misc.models import File
from misc.fields import ContentField


class BadgeSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default='badge', read_only=True)
    content = ContentField()
    image = FileSerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        source='image',
        queryset=File.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Badge
        fields = '__all__'
