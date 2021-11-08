from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Chapter, Resource
from .serializers import ChapterSerializer, ResourceSerializer


class ResourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows resources to be viewed or edited.
    """

    queryset = Resource.templates.all()
    serializer_class = ResourceSerializer

    def _save_recursive_items(self, items, resource, parent_chapter):
        for i in items:
            chapter_serializer = ChapterSerializer(data=i)
            chapter_serializer.is_valid(raise_exception=True)
            p = chapter_serializer.save(resource=resource, parent_chapter=parent_chapter)

            if "chapters" in i:
                self._save_recursive_items(i["chapters"], resource, p)

    def create(self, request, *args, **kwargs):
        # remove for creating a duplicate
        if "id" in request.data:
            del request.data["id"]
        resource_serializer = self.serializer_class(data=request.data)
        resource_serializer.is_valid(raise_exception=True)
        resource = resource_serializer.save()
        self._save_recursive_items(request.data["chapters"], resource, None)
        b = self.serializer_class(resource)
        return Response(b.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        Chapter.objects.filter(resource=instance).delete()
        self._save_recursive_items(request.data["chapters"], instance, None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
