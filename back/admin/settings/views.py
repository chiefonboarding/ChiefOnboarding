from datetime import datetime

import pyotp
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from admin.integrations.models import (
    INTEGRATION_OPTIONS,
    INTEGRATION_OPTIONS_URLS,
    AccessToken,
)
from organization.models import (
    LANGUAGES_OPTIONS,
    Changelog,
    Organization,
    WelcomeMessage,
)
from users.mixins import AdminPermMixin, LoginRequiredMixin
from slack_bot.models import SlackChannel

from .forms import (
    AdministratorsCreateForm,
    AdministratorsUpdateForm,
    OrganizationGeneralForm,
    OTPVerificationForm,
    WelcomeMessagesUpdateForm,
)


class OrganizationGeneralUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_general_update.html"
    form_class = OrganizationGeneralForm
    success_url = reverse_lazy("settings:general")
    success_message = "Organization info has been updated"

    def get_object(self):
        return Organization.object.get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "General Updates"
        context["subtitle"] = "settings"
        return context


class AdministratorListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "settings_admins.html"
    queryset = get_user_model().admins.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Administrators"
        context["subtitle"] = "settings"
        context["add_action"] = reverse_lazy("settings:administrators-create")
        return context


class AdministratorCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "settings_admins_create.html"
    queryset = get_user_model().admins.all()
    form_class = AdministratorsCreateForm
    success_url = reverse_lazy("settings:administrators")
    success_message = "Admin has been created"

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        user = get_user_model().objects.filter(email=form.cleaned_data["email"])
        if user.exists():
            # Change user if user already exists
            user.role = form.cleaned_data["role"]
            user.save()
        else:
            form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Administrator"
        context["subtitle"] = "settings"
        return context


class AdministratorUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "settings_admins_update.html"
    queryset = get_user_model().admins.all()
    form_class = AdministratorsUpdateForm
    success_url = reverse_lazy("settings:administrators")
    success_message = "Admin has been changed"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Change Administrator"
        context["subtitle"] = "settings"
        return context


class AdministratorDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = get_user_model().admins.all()
    success_url = reverse_lazy("settings:administrators")


class WelcomeMessageUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "org_welcome_message_update.html"
    form_class = WelcomeMessagesUpdateForm
    success_message = "Message has been updated"

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return WelcomeMessage.objects.get(
            language=self.kwargs.get("language"), message_type=self.kwargs.get("type")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["languages"] = LANGUAGES_OPTIONS
        context["types"] = WelcomeMessage.MESSAGE_TYPE
        context["title"] = "Update welcome messages"
        context["subtitle"] = "settings"
        return context


class PersonalLanguageUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "personal_language_update.html"
    model = get_user_model()
    fields = [
        "language",
    ]
    success_message = "Your default language has been updated"

    def get_success_url(self):
        return self.request.path

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update your default language"
        context["subtitle"] = "settings"
        return context


class OTPView(LoginRequiredMixin, AdminPermMixin, FormView):
    template_name = "personal_otp.html"
    form_class = OTPVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.requires_otp = True
        user.save()
        keys = user.reset_otp_recovery_keys()
        return render(
            self.request,
            "personal_otp.html",
            {"title": "TOTP 2FA", "subtitle": "settings", "keys": keys},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.requires_otp:
            context["otp_url"] = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
                name=user.email, issuer_name="ChiefOnboarding"
            )
        context["title"] = "Enable TOTP 2FA" if not user.requires_otp else "TOTP 2FA"
        context["subtitle"] = "settings"
        return context


class IntegrationsListView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "settings_integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Integrations"
        context["subtitle"] = "settings"
        for idx, integration in enumerate(INTEGRATION_OPTIONS_URLS):
            integration["name"] = INTEGRATION_OPTIONS[idx][1]
            integration["obj"] = AccessToken.objects.filter(
                integration=INTEGRATION_OPTIONS[idx][0], active=True
            ).first()

        context["integrations"] = INTEGRATION_OPTIONS_URLS
        # context["integrations"].sort(key=lambda x: x["name"].lower())
        return context


class GoogleLoginSetupView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    model = AccessToken
    fields = ["client_id", "client_secret"]
    success_message = "You can now login with your Google account"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Google login button setup"
        context["subtitle"] = "settings"
        context["button_text"] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=3).delete()
        form.instance.integration = 3
        return super().form_valid(form)


class AsanaSetupView(LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin):
    template_name = "token_create.html"
    model = AccessToken
    fields = ["token"]
    success_message = "Your Asana integration has been set up!"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Asana setup"
        context["subtitle"] = "settings"
        context["button_text"] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=4).delete()
        form.instance.integration = 4
        return super().form_valid(form)


class GoogleAccountCreationSetupView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    model = AccessToken
    fields = ["client_id", "client_secret"]
    success_message = "You can now automatically create accounts for users"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Google auto account create setup"
        context["subtitle"] = "settings"
        context["button_text"] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=2).delete()
        form.instance.integration = 2
        return super().form_valid(form)


class SlackAccountCreationSetupView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    model = AccessToken
    fields = [
        "app_id",
        "client_id",
        "client_secret",
        "signing_secret",
        "verification_token",
    ]
    success_message = "You can now automatically create Slack accounts for new hires"
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Slack auto account create setup"
        context["subtitle"] = "settings"
        context["button_text"] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=1).delete()
        form.instance.integration = 1
        return super().form_valid(form)


class SlackBotSetupView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    model = AccessToken
    fields = [
        "app_id",
        "client_id",
        "client_secret",
        "signing_secret",
        "verification_token",
    ]
    success_message = (
        "Slack has now been connected, check if you got a message from your bot!"
    )
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Slack bot setup"
        context["subtitle"] = "settings"
        context["button_text"] = "Enable"
        return context

    def form_valid(self, form):
        AccessToken.objects.filter(integration=0).delete()
        form.instance.integration = 0
        return super().form_valid(form)


class SlackChannelsUpdateView(LoginRequiredMixin, AdminPermMixin, RedirectView):
    permanent = False
    pattern_name = "settings:integrations"

    def get(self, request, *args, **kwargs):
        SlackChannel.objects.update_channels()
        print("got here")
        messages.success(
            request,
            "Newly added channels have been added. Make sure the bot has been added to that channel too if you want it to post/get info there!",
        )
        return super().get(request, *args, **kwargs)


class IntegrationDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    """This is a general delete function for all integrations"""

    template_name = "integration-delete.html"
    model = AccessToken
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete integration"
        context["subtitle"] = "settings"
        return context


class ChangelogListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "changelog.html"
    model = Changelog

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["date_last_checked"] = user.seen_updates
        user.seen_updates = datetime.now().date()
        user.save()
        context["title"] = "Changelog"
        return context
