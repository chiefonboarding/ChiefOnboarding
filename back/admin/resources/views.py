from admin.resources.selectors import get_resource_templates_for_user
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from misc.mixins import FormWithUserContextMixin
from users.mixins import AdminOrManagerPermMixin

from .forms import ResourceForm
from .models import Resource


class ResourceListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_resource_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Resource items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("resources:create")
        return context


class ResourceCreateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, CreateView):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    success_message = _("Resource item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create resource item")
        context["subtitle"] = _("templates")
        return context


class ResourceUpdateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, UpdateView):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    success_message = _("Resource item has been updated")

    def get_queryset(self):
        return get_resource_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update resource item")
        context["subtitle"] = _("templates")
        return context


class ResourceDeleteView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("resources:list")
    success_message = _("Resource item has been removed")

    def get_queryset(self):
        return get_resource_templates_for_user(user=self.request.user)
