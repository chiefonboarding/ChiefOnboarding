from rest_framework import serializers
from django import forms
from django.forms import TextInput

from .models import Content, File
from .serializers import ContentPostSerializer, ContentSerializer


class ContentField(serializers.Field):
    def to_representation(self, value):
        return ContentSerializer(value, many=True).data

    def to_internal_value(self, data):
        all_values = []
        for i in data:
            files = i.pop("files", [])
            i["content"] = i["content"].replace("<br>", "")
            serializer = ContentPostSerializer(data=i)
            serializer.is_valid(raise_exception=True)
            item = serializer.save()
            for j in files:
                item.files.add(File.objects.get(id=j["id"]))
            all_values.append(item)
        return all_values


class WYSIWYGInput(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget as an HTML string."""
        context = self.get_context(name, ContentSerializer(value, many=True).data, attrs)
        return self._render("wysiwyg_field.html", context, renderer)


class ContentFormField(forms.Field):
    widget = WYSIWYGInput

    def to_python(self, value):
        return ContentSerializer(value, many=True).data

    def to_internal_value(self, data):
        hello = 0/0
        all_values = []
        for i in data:
            files = i.pop("files", [])
            i["content"] = i["content"].replace("<br>", "")
            serializer = ContentPostSerializer(data=i)
            serializer.is_valid(raise_exception=True)
            item = serializer.save()
            for j in files:
                item.files.add(File.objects.get(id=j["id"]))
            all_values.append(item)
        return all_values
