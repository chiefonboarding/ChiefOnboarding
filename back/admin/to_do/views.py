from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminOrManagerPermMixin

from .forms import ToDoForm
from .models import ToDo


class ToDoListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = ToDo.templates.all().order_by("name").defer("content")
    paginate_by = settings.TODO_PAGINATE_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("To do items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("todo:create")
        return context


class ToDoCreateView(AdminOrManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "template_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    success_message = _("To do item has been created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create to do item")
        context["subtitle"] = _("templates")
        return context


class ToDoUpdateView(AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView):
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


class ToDoDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    queryset = ToDo.objects.all()
    success_url = reverse_lazy("todo:list")
    success_message = _("To do item has been removed")
