from datetime import datetime
import pyotp
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView

from organization.models import Organization, WelcomeMessage, Changelog, LANGUAGES_OPTIONS
from .forms import OrganizationGeneralForm, AdministratorsCreateForm, WelcomeMessagesUpdateForm, OTPVerificationForm
from admin.integrations.models import INTEGRATION_OPTIONS, INTEGRATION_OPTIONS_URLS, AccessToken


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
    template_name = "personal_language_update.html"
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


class OTPView(FormView):
    template_name = "personal_otp.html"
    form_class = OTPVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.requires_otp = True
        user.save()
        keys = user.reset_otp_recovery_keys()
        return render(self.request, "personal_otp.html", {'title': 'TOTP 2FA', 'subtitle': 'settings', 'keys': keys})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.requires_otp:
            context['otp_url'] = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
                name=user.email, issuer_name="ChiefOnboarding"
            )
        context['title'] = "Enable TOTP 2FA" if not user.requires_otp else "TOTP 2FA"
        context['subtitle'] = "settings"
        return context


class IntegrationsListView(TemplateView):
    template_name = "settings_integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Integrations"
        context['subtitle'] = "settings"
        context['integrations'] = [
            {
                "name": integration[1],
                'obj': AccessToken.objects.filter(integration=integration[0], active=True).first(),
                'create_url': INTEGRATION_OPTIONS_URLS[idx][0],
            }
            for idx, integration in enumerate(INTEGRATION_OPTIONS)
        ]
        context['integrations'].sort(key=lambda x: x['name'].lower())
        return context


class GoogleLoginSetupView(CreateView, SuccessMessageMixin):
    template_name = "org_general_update.html"
    model = AccessToken
    fields = ["client_id", "client_secret"]
    success_message = "You can now login with your Google account"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Google login button setup"
        context['subtitle'] = "settings"
        context['button_text'] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=3).delete()
        form.instance.integration = 3
        return super().form_valid(form)


class GoogleAccountCreationSetupView(CreateView, SuccessMessageMixin):
    template_name = "org_general_update.html"
    model = AccessToken
    fields = ["client_id", "client_secret"]
    success_message = "You can now automatically create accounts for users"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Google auto account create setup"
        context['subtitle'] = "settings"
        context['button_text'] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=2).delete()
        form.instance.integration = 2
        return super().form_valid(form)


class SlackAccountCreationSetupView(CreateView, SuccessMessageMixin):
    template_name = "org_general_update.html"
    model = AccessToken
    fields = ["app_id", "client_id", "client_secret", "signing_secret", "verification_token"]
    success_message = "You can now automatically create Slack accounts for new hires"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Slack auto account create setup"
        context['subtitle'] = "settings"
        context['button_text'] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=1).delete()
        form.instance.integration = 1
        return super().form_valid(form)


class SlackBotSetupView(CreateView, SuccessMessageMixin):
    template_name = "org_general_update.html"
    model = AccessToken
    fields = ["app_id", "client_id", "client_secret", "signing_secret", "verification_token"]
    success_message = "Slack has now been connected, check if you got a message from your bot!"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Slack bot setup"
        context['subtitle'] = "settings"
        context['button_text'] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=0).delete()
        form.instance.integration = 0
        return super().form_valid(form)


class IntegrationDeleteView(DeleteView):
    """ This is a general delete function for all integrations """

    template_name = "integration-delete.html"
    model = AccessToken
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete integration"
        context['subtitle'] = "settings"
        return context


class ChangelogListView(ListView):
    template_name = "changelog.html"
    model = Changelog

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['date_last_checked'] = user.seen_updates
        user.seen_updates = datetime.now().date()
        user.save()
        context['title'] = "Changelog"
        return context
