from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.hardware.forms import HardwareForm
from admin.hardware.models import Hardware
from users.mixins import AdminOrManagerPermMixin


class HardwareListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = Hardware.templates.all().order_by("name").defer("content")
    paginate_by = settings.HARDWARE_PAGINATE_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Hardware items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("hardware:create")
        return context


class HardwareCreateView(AdminOrManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "template_update.html"
    form_class = HardwareForm
    success_url = reverse_lazy("hardware:list")
    success_message = _("Hardware item has been created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create hardware item")
        context["subtitle"] = _("templates")
        return context


class HardwareUpdateView(AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "template_update.html"
    form_class = HardwareForm
    success_url = reverse_lazy("hardware:list")
    queryset = Hardware.templates.all()
    success_message = _("Hardware item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update hardware item")
        context["subtitle"] = _("templates")
        return context


class HardwareDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    queryset = Hardware.objects.all()
    success_url = reverse_lazy("hardware:list")
    success_message = _("Hardware item has been removed")
