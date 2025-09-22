from admin.introductions.selectors import get_intro_templates_for_user
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from misc.mixins import FormWithUserContextMixin
from users.mixins import AdminOrManagerPermMixin
from users.models import User

from .forms import IntroductionForm


class IntroductionListView(AdminOrManagerPermMixin, ListView):
    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_intro_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Introduction items")
        context["subtitle"] = _("templates")
        context["add_action"] = reverse_lazy("introductions:create")
        return context


class IntroductionCreateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, CreateView):
    template_name = "intro_update.html"
    form_class = IntroductionForm
    success_url = reverse_lazy("introductions:list")
    success_message = _("Introduction item has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create introduction item")
        context["subtitle"] = _("templates")
        return context


class IntroductionColleaguePreviewView(AdminOrManagerPermMixin, DetailView):
    template_name = "_colleague_intro.html"
    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["intro_person"] = context["object"]
        return context


class IntroductionUpdateView(AdminOrManagerPermMixin, FormWithUserContextMixin, SuccessMessageMixin, UpdateView):
    template_name = "intro_update.html"
    form_class = IntroductionForm
    success_url = reverse_lazy("introductions:list")
    success_message = _("Introduction item has been updated")

    def get_queryset(self):
        return get_intro_templates_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update introduction item")
        context["subtitle"] = _("templates")
        return context


class IntroductionDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("introductions:list")
    success_message = _("Introduction item has been removed")

    def get_queryset(self):
        return get_intro_templates_for_user(user=self.request.user)
