from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import ToDoForm
from .models import ToDo


class ToDoListView(ListView):
    template_name = "templates.html"
    queryset = ToDo.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "To do items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("todo:create")
        context["wysiwyg"] = []
        return context


class ToDoCreateView(SuccessMessageMixin, CreateView):
    template_name = "todo_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    success_message = "To do item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create to do item"
        context["subtitle"] = "templates"
        return context


class ToDoUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "todo_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    queryset = ToDo.templates.all()
    success_message = "To do item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update to do item"
        context["subtitle"] = "templates"
        context["wysiwyg"] = context["todo"].content_json
        return context


class ToDoDeleteView(DeleteView):
    queryset = ToDo.objects.all()
    success_url = reverse_lazy("todo:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "To do item has been removed")
        return response
