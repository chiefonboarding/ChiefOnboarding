from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import NoteSerializer

from .models import Note


class NoteViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows notes to be deleted.
    """
    serializer_class = NoteSerializer
    queryset = Note.objects.select_related('new_hire', 'admin').all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # prevent others from removing the comment
        if instance.admin == request.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

