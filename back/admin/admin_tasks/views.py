from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.views.generic.base import TemplateView, RedirectView
from rest_framework.response import Response

from users import permissions

from .forms import AdminTaskCommentForm, AdminTaskUpdateForm, AdminTaskCreateForm
from .models import AdminTask, AdminTaskComment
from .serializers import (AdminTaskSerializer, CommentPostSerializer,
                          CommentSerializer)
from users.mixins import LoginRequiredMixin, ManagerPermMixin


class MyAdminTasksListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "admin_tasks_yours.html"
    paginate_by = 10

    def get_queryset(self):
        return AdminTask.objects.filter(assigned_to=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Your tasks"
        context["subtitle"] = "Tasks"
        context["add_action"] = reverse_lazy("admin_tasks:create")
        return context


class AllAdminTasksListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "admin_tasks_all.html"
    paginate_by = 10

    def get_queryset(self):
        return AdminTask.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "All tasks"
        context["subtitle"] = "Tasks"
        context["add_action"] = reverse_lazy("admin_tasks:create")
        return context


class AdminTaskToggleDoneView(LoginRequiredMixin, ManagerPermMixin, RedirectView):
    permanent = False
    pattern_name = "admin_tasks:detail"

    def get(self, request, *args, **kwargs):
        task_id = self.kwargs.get("pk", -1)
        admin_task = get_object_or_404(AdminTask, id=task_id)
        admin_task.completed = not admin_task.completed
        admin_task.save()
        return super().get(request, *args, **kwargs)


class AdminTasksUpdateView(LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "admin_tasks_detail.html"
    form_class = AdminTaskUpdateForm
    model = AdminTask
    success_message = "Task has been updated"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        context["object"] = task
        context["title"] = f"Task: {task.name}"
        context["subtitle"] = "Tasks"
        context["comment_form"] = AdminTaskCommentForm
        return context


class AdminTasksCreateView(LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "admin_tasks_create.html"
    form_class = AdminTaskCreateForm
    model = AdminTask
    success_message = "Task has been created"
    success_url = reverse_lazy("admin_tasks:all")

    def form_valid(self, form):
        self.object = form.save()
        AdminTaskComment.objects.create(
            admin_task=self.object,
            content=form.cleaned_data['comment'],
            comment_by=self.request.user
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New task"
        context["subtitle"] = "Tasks"
        return context


class AdminTasksCommentCreateView(LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "admin_tasks_detail.html"
    model = AdminTaskComment
    fields = [
        "content",
    ]
    success_message = "Comment has been posted"

    def get_success_url(self):
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        return reverse("admin_tasks:detail", args=[task.id])

    def form_valid(self, form):
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        form.instance.comment_by = self.request.user
        form.instance.admin_task = task
        return super().form_valid(form)


class AdminTaskViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.ManagerPermission,)
    queryset = AdminTask.objects.all().select_related("new_hire", "assigned_to").prefetch_related("comment")
    serializer_class = AdminTaskSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_task = serializer.save()

        if "comment" in request.data:
            comment = CommentPostSerializer(data={"content": request.data["comment"]})
            if comment.is_valid():
                comment.save(admin_task=admin_task, comment_by=request.user)

        if request.user != admin_task.assigned_to:
            admin_task.send_notification_new_assigned()
        return Response({"id": admin_task.id}, status=status.HTTP_201_CREATED)

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


