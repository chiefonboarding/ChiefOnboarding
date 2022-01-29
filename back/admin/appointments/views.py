from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminPermMixin, LoginRequiredMixin

from .forms import AppointmentForm
from .models import Appointment


class AppointmentListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Appointment.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Appointment items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("appointments:create")
        return context


class AppointmentCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "todo_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    success_message = "Appointment item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create appointment item"
        context["subtitle"] = "templates"
        return context


class AppointmentUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "todo_update.html"
    form_class = AppointmentForm
    success_url = reverse_lazy("appointments:list")
    queryset = Appointment.templates.all()
    success_message = "Appointment item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update appointment item"
        context["subtitle"] = "templates"
        return context


class AppointmentDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Appointment.objects.all()
    success_url = reverse_lazy("appointments:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Appointment item has been removed")
        return response
