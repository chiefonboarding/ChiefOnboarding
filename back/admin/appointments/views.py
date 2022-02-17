from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminPermMixin, LoginRequiredMixin
from django.utils.translation import ugettext as _

from .forms import AppointmentForm
from .models import Appointment


class AppointmentListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Appointment.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Appointment items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("appointments:create")
        return context


class AppointmentCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "todo_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    success_message = _("Appointment item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create appointment item")
        context["subtitle"] = _("templates")
        return context


class AppointmentUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "todo_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    queryset = Appointment.templates.all()
    success_message = _("Appointment item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update appointment item")
        context["subtitle"] = _("templates")
        return context


class AppointmentDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Appointment.objects.all()
    success_url = reverse_lazy("appointments:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("Appointment item has been removed"))
        return response
