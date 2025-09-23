from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.preboarding.selectors import get_preboarding_templates_for_user
from misc.mixins import FormWithUserContextMixin
from users.mixins import AdminOrManagerPermMixin

from .forms import PreboardingForm


class PreboardingListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_preboarding_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Preboarding items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("preboarding:create")
        return context


class PreboardingCreateView(
    AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, CreateView
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
    AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, UpdateView
):
    template_name = "template_update.html"
    form_class = PreboardingForm
    success_url = reverse_lazy("preboarding:list")
    success_message = _("Preboarding item has been updated")

    def get_queryset(self):
        return get_preboarding_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update preboarding item")
        context["subtitle"] = _("templates")
        return context


class PreboardingDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("preboarding:list")
    success_message = _("Sequence item has been removed")

    def get_queryset(self):
        return get_preboarding_templates_for_user(user=self.request.user)
