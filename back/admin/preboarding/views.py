from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import ManagerPermMixin

from .forms import PreboardingForm
from .models import Preboarding


class PreboardingListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = Preboarding.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Preboarding items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("preboarding:create")
        return context


class PreboardingCreateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "template_update.html"
    form_class = PreboardingForm
    success_url = reverse_lazy("preboarding:list")
    success_message = _("Preboarding item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create preboarding item")
        context["subtitle"] = _("templates")
        return context


class PreboardingUpdateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "template_update.html"
    form_class = PreboardingForm
    success_url = reverse_lazy("preboarding:list")
    queryset = Preboarding.templates.all()
    success_message = _("Preboarding item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update preboarding item")
        context["subtitle"] = _("templates")
        return context


class PreboardingDeleteView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, DeleteView
):
    queryset = Preboarding.objects.all()
    success_url = reverse_lazy("preboarding:list")
    success_message = _("Sequence item has been removed")
