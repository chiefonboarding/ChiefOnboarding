from admin.appointments.selectors import get_appointment_templates_for_user
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from misc.mixins import FormWithUserContextMixin
from users.mixins import AdminOrManagerPermMixin

from .forms import AppointmentForm


class AppointmentListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_appointment_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Appointment items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("appointments:create")
        return context


class AppointmentCreateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, CreateView):
    template_name = "template_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    success_message = _("Appointment item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create appointment item")
        context["subtitle"] = _("templates")
        return context


class AppointmentUpdateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, UpdateView):
    template_name = "template_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    success_message = _("Appointment item has been updated")
    
    def get_queryset(self):
        return get_appointment_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update appointment item")
        context["subtitle"] = _("templates")
        return context


class AppointmentDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("appointments:list")
    success_message = _("Appointment item has been removed")

    def get_queryset(self):
        return get_appointment_templates_for_user(user=self.request.user)
