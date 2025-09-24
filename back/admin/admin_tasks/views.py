from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminOrManagerPermMixin

from .forms import AdminTaskCommentForm, AdminTaskCreateForm, AdminTaskUpdateForm
from .models import AdminTask, AdminTaskComment


class MyAdminTasksListView(AdminOrManagerPermMixin, ListView):
    template_name = "admin_tasks_yours.html"
    paginate_by = 10

    def get_queryset(self):
        return AdminTask.objects.filter(assigned_to=self.request.user).select_related(
            "new_hire", "assigned_to"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Your tasks"
        context["subtitle"] = "Tasks"
        context["add_action"] = reverse_lazy("admin_tasks:create")
        return context


class AllAdminTasksListView(AdminOrManagerPermMixin, ListView):
    template_name = "admin_tasks_all.html"
    paginate_by = 10

    def get_queryset(self):
        return AdminTask.objects.all().select_related("new_hire", "assigned_to")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "All tasks"
        context["subtitle"] = "Tasks"
        context["add_action"] = reverse_lazy("admin_tasks:create")
        return context


class AdminTaskCompleteView(AdminOrManagerPermMixin, BaseDetailView):
    model = AdminTask

    def post(self, request, *args, **kwargs):
        admin_task = self.get_object()
        admin_task.mark_completed()
        return redirect("admin_tasks:detail", pk=admin_task.id)


class AdminTasksCreateView(AdminOrManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "admin_tasks_create.html"
    form_class = AdminTaskCreateForm
    model = AdminTask
    success_message = _("Task has been created")
    success_url = reverse_lazy("admin_tasks:all")

    def form_valid(self, form):
        self.object = form.save()
        AdminTaskComment.objects.create(
            admin_task=self.object,
            content=form.cleaned_data["comment"],
            comment_by=self.request.user,
        )
        # Send message to person that got assigned to this
        if self.request.user.id != form.cleaned_data["assigned_to"].id:
            self.object.send_notification_new_assigned()

        # Send notification based on extra notification option
        self.object.send_notification_third_party()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New task")
        context["subtitle"] = _("Tasks")
        return context


class AdminTasksUpdateView(AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "admin_tasks_detail.html"
    form_class = AdminTaskUpdateForm
    model = AdminTask
    success_message = _("Task has been updated")

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        context["object"] = task
        context["title"] = _("Task: %(name)s") % {"name": task.name}
        context["subtitle"] = _("Tasks")
        context["comment_form"] = AdminTaskCommentForm
        return context

    def form_valid(self, form):
        # send email/bot message to newly assigned person
        initial_assigned_to = AdminTask.objects.get(id=form.instance.id).assigned_to
        form.save()
        if (
            form.cleaned_data["assigned_to"] != initial_assigned_to
            and form.cleaned_data["assigned_to"] != self.request.user
        ):
            form.instance.send_notification_new_assigned()
        return super().form_valid(form)


class AdminTasksCommentCreateView(
    AdminOrManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "admin_tasks_detail.html"
    model = AdminTaskComment
    fields = [
        "content",
    ]
    success_message = _("Comment has been posted")

    def get_success_url(self):
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        return reverse("admin_tasks:detail", args=[task.id])

    def form_valid(self, form):
        task = get_object_or_404(AdminTask, pk=self.kwargs.get("pk"))
        # Can't post comments when item is completed
        if task.completed:
            raise Http404
        form.instance.comment_by = self.request.user
        form.instance.admin_task = task
        item = form.save()
        item.send_notification_new_message()
        return super().form_valid(form)
