from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminPermMixin, LoginRequiredMixin

from .forms import BadgeForm
from .models import Badge


class BadgeListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Badge.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Badge items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("badges:create")
        return context


class BadgeCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "todo_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    success_message = _("badge item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "todo_update.html"
    form_class = BadgeForm
    success_url = reverse_lazy("badges:list")
    queryset = Badge.templates.all()
    success_message = _("Badge item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update badge item")
        context["subtitle"] = _("templates")
        return context


class BadgeDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Badge.objects.all()
    success_url = reverse_lazy("badges:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("badge item has been removed"))
        return response
