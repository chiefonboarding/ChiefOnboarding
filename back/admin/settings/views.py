from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView

from organization.models import Organization, WelcomeMessage, LANGUAGES_OPTIONS
from .forms import OrganizationGeneralForm, AdministratorsCreateForm, WelcomeMessagesUpdateForm


class OrganizationGeneralUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "org_general_update.html"
    form_class = OrganizationGeneralForm
    success_url = reverse_lazy("settings:general")
    success_message = "Organization info has been updated"

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "General Updates"
        context['subtitle'] = "settings"
        return context


class AdministratorListView(ListView):
    template_name = "settings_admins.html"
    queryset = get_user_model().admins.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Administrators"
        context['subtitle'] = "settings"
        context['add_action'] = reverse_lazy("settings:administrators-create")
        return context


class AdministratorCreateView(SuccessMessageMixin, CreateView):
    template_name = "settings_admins_create.html"
    queryset = get_user_model().admins.all()
    form_class = AdministratorsCreateForm
    success_url = reverse_lazy("settings:administrators")
    success_message = "Admin has been created"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add Administrator"
        context['subtitle'] = "settings"
        return context


class AdministratorDeleteView(DeleteView):
    queryset = get_user_model().admins.all()
    success_url = reverse_lazy("settings:administrators")


class WelcomeMessageUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "org_welcome_message_update.html"
    form_class = WelcomeMessagesUpdateForm
    success_message = "Message has been updated"

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return WelcomeMessage.objects.get(
            language=self.kwargs.get("language"),
            message_type=self.kwargs.get("type")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = LANGUAGES_OPTIONS
        context['types'] = WelcomeMessage.MESSAGE_TYPE
        context['title'] = "Update welcome messages"
        context['subtitle'] = "settings"
        return context


class PersonalLanguageUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "org_personal_language_update.html"
    model = get_user_model()
    fields = ["language",]
    success_message = "Your default language has been updated"

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Update your default language"
        context['subtitle'] = "settings"
        return context
