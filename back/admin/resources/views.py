from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import ManagerPermMixin

from .forms import ResourceForm
from .models import Resource


class ResourceListView(ManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = Resource.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Resource items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("resources:create")
        return context


class ResourceCreateView(ManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    success_message = _("Resource item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create resource item")
        context["subtitle"] = _("templates")
        return context


class ResourceUpdateView(ManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    queryset = Resource.templates.all()
    success_message = _("Resource item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update resource item")
        context["subtitle"] = _("templates")
        return context


class ResourceDeleteView(ManagerPermMixin, SuccessMessageMixin, DeleteView):
    queryset = Resource.objects.all()
    success_url = reverse_lazy("resources:list")
    success_message = _("Resource item has been removed")
