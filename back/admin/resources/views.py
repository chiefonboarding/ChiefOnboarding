from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import ResourceForm
from .models import Resource


class ResourceListView(ListView):
    template_name = "templates.html"
    queryset = Resource.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Resource items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("resources:create")
        context["wysiwyg"] = []
        return context


class ResourceCreateView(SuccessMessageMixin, CreateView):
    template_name = "todo_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    success_message = "Resource item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create resource item"
        context["subtitle"] = "templates"
        return context


class ResourceUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "todo_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    queryset = Resource.templates.all()
    success_message = "Resource item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update resource item"
        context["subtitle"] = "templates"
        # context["wysiwyg"] = context["resource"].content_json
        return context


class ResourceDeleteView(DeleteView):
    queryset = Resource.objects.all()
    success_url = reverse_lazy("resources:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Resource item has been removed")
        return response
