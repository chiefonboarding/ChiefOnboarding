from django import forms
from django.forms import TextInput
from rest_framework import serializers

from .models import Content, File
from .serializers import ContentPostSerializer, ContentSerializer

from django.db.models import JSONField

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


class ContentJSONField(JSONField):
    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if 'blocks' not in value:
            return value

        for block in value['blocks']:
            if block['type'] in ['file', 'image']:
                block['data']['file']['url'] = File.objects.get(id=block['data']['file']['id']).get_url()
        return value


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
        hello = 0 / 0
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
