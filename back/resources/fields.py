from rest_framework import serializers
from .models import Category


class CategoryField(serializers.Field):

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        if data.strip() == '':
            return None
        c, created = Category.objects.get_or_create(name=data)
        return c