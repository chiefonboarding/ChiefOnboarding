from rest_framework import serializers
from .models import Note
from users.serializers import NewHireSerializer, AdminSerializer


class NoteSerializer(serializers.ModelSerializer):
    new_hire = NewHireSerializer(read_only=True)
    admin = AdminSerializer(read_only=True)

    class Meta:
        model = Note
        fields = '__all__'
