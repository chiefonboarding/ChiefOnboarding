from rest_framework.response import Response
from rest_framework import status
from .models import AdminTask
from rest_framework import viewsets
from users import permissions
from rest_framework.decorators import action

from .serializers import CommentPostSerializer, AdminTaskSerializer, CommentSerializer


class AdminTaskViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.ManagerPermission,)
    queryset = AdminTask.objects.all()
    serializer_class = AdminTaskSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_task = serializer.save()

        if 'comment' in request.data:
            comment = CommentPostSerializer(data=request.data)
            if comment.is_valid():
                comment.save(admin_task=admin_task, comment_by=request.user)

        if request.user != admin_task.assigned_to:
            admin_task.send_notification_new_assigned()
        return Response({'id': admin_task.id}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        # send email/bot message to newly assigned person
        if serializer.data.assigned_to.id != instance.assigned_to.id:
            self.perform_update(serializer)
            instance.send_notification_new_assigned()

        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True)
    def complete(self, request, pk):
        task = self.get_object()
        task.completed = not task.completed
        task.save()
        return Response({'completed': task.completed})

    @action(detail=True, methods=['POST'])
    def add_comment(self, request, pk):
        task = self.get_object()
        serializer = CommentPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(admin_task=task, comment_by=request.user)
        comment = CommentSerializer(task.comment.last())
        return Response(comment.data)

    @action(detail=False, methods=['GET'])
    def done(self, request):
        tasks = self.get_serializer(AdminTask.objects.filter(completed=True), many=True)
        return Response(tasks.data)

    @action(detail=False, methods=['GET'])
    def done_by_user(self, request):
        tasks = self.get_serializer(AdminTask.objects.filter(completed=True, assigned_to=request.user), many=True)
        return Response(tasks.data)
