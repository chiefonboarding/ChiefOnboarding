from rest_framework import serializers
from .models import Preboarding
from misc.fields import ContentField


class PreboardingSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default='preboarding', read_only=True)
    id = serializers.IntegerField(required=False)
    content = ContentField()

    class Meta:
        model = Preboarding
        fields = '__all__'
