from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.badges.selectors import get_badge_templates_for_user
from misc.mixins import FormWithUserContextMixin
from users.mixins import AdminOrManagerPermMixin

from .forms import BadgeForm


class BadgeListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_badge_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Badge items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("badges:create")
        return context


class BadgeCreateView(
    AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, CreateView
):
    template_name = "template_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    success_message = _("badge item has been updated")

    def get_queryset(self):
        return get_badge_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeUpdateView(
    AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, UpdateView
):
    template_name = "template_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    success_message = _("Badge item has been updated")

    def get_queryset(self):
        return get_badge_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("badges:list")
    success_message = _("badge item has been removed")

    def get_queryset(self):
        return get_badge_templates_for_user(user=self.request.user)
