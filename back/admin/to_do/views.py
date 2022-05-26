from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import LoginRequiredMixin, ManagerPermMixin

from .forms import ToDoForm
from .models import ToDo


class ToDoListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = ToDo.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("To do items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("todo:create")
        return context


class ToDoCreateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "template_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    success_message = _("To do item has been created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create to do item")
        context["subtitle"] = _("templates")
        return context


class ToDoUpdateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "template_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    queryset = ToDo.templates.all()
    success_message = _("To do item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update to do item")
        context["subtitle"] = _("templates")
        return context


class ToDoDeleteView(LoginRequiredMixin, ManagerPermMixin, DeleteView):
    queryset = ToDo.objects.all()
    success_url = reverse_lazy("todo:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("To do item has been removed"))
        return response
