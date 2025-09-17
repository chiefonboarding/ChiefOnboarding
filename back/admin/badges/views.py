from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import ManagerPermMixin

from .forms import BadgeForm
from .models import Badge


class BadgeListView(ManagerPermMixin, ListView):
    template_name = "templates.html"
    queryset = Badge.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Badge items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("badges:create")
        return context


class BadgeCreateView(ManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "template_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    success_message = _("badge item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeUpdateView(ManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "template_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    queryset = Badge.templates.all()
    success_message = _("Badge item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeDeleteView(ManagerPermMixin, SuccessMessageMixin, DeleteView):
    queryset = Badge.objects.all()
    success_url = reverse_lazy("badges:list")
    success_message = _("badge item has been removed")
