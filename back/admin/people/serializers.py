from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email", "role")
