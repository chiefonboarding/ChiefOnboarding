from rest_framework import serializers

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
