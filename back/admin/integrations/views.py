import json
from datetime import timedelta
from urllib.parse import urlparse

import requests
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminPermMixin, LoginRequiredMixin, ManagerPermMixin

from .forms import IntegrationExtraArgsForm, IntegrationForm
from .models import Integration, IntegrationTracker


class IntegrationCreateView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    form_class = IntegrationForm
    success_message = _("Integration has been created!")
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Add new integration")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Create")
        return context

    def form_valid(self, form):
        form.instance.integration = Integration.Type.CUSTOM
        return super().form_valid(form)


class IntegrationCreateGoogleLoginView(
    LoginRequiredMixin, AdminPermMixin, CreateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    fields = ["client_id", "client_secret"]
    queryset = Integration.objects.filter(integration=Integration.Type.GOOGLE_LOGIN)
    success_message = _("Integration has been updated!")
    success_url = reverse_lazy("settings:integrations")

    def form_valid(self, form):
        form.instance.integration = Integration.Type.GOOGLE_LOGIN
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Change Google login credentials")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Update")
        return context


class IntegrationUpdateView(
    LoginRequiredMixin, AdminPermMixin, UpdateView, SuccessMessageMixin
):
    template_name = "token_create.html"
    form_class = IntegrationForm
    queryset = Integration.objects.filter(integration=Integration.Type.CUSTOM)
    success_message = _("Integration has been updated!")
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update existing integration")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Update")
        return context

    def form_valid(self, form):
        new_initial_data = form.cleaned_data["manifest"].get("initial_data_form", [])
        old_initial_data = self.get_object().manifest.get("initial_data_form", [])

        # remove keys that don't exist anymore from saved secrets
        new_initial_data_keys = [item["id"] for item in new_initial_data]
        for item in old_initial_data:
            if item["id"] not in new_initial_data_keys:
                form.instance.extra_args.pop(item["id"], None)

        return super().form_valid(form)


class IntegrationDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    """This is a general delete function for all integrations"""

    template_name = "integration-delete.html"
    model = Integration
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete integration")
        context["subtitle"] = _("settings")
        return context


class IntegrationUpdateExtraArgsView(
    LoginRequiredMixin, AdminPermMixin, UpdateView, SuccessMessageMixin
):
    template_name = "update_initial_data_form.html"
    form_class = IntegrationExtraArgsForm
    queryset = Integration.objects.filter(integration=Integration.Type.CUSTOM)
    success_message = _("Your config values have been updated!")
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Integration settings")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Update")
        return context


class IntegrationDeleteExtraArgsView(
    LoginRequiredMixin, AdminPermMixin, DeleteView, SuccessMessageMixin
):
    template_name = "update_initial_data_form.html"
    queryset = Integration.objects.filter(integration=Integration.Type.CUSTOM)
    success_message = _("Secret value has been removed")
    success_url = reverse_lazy("settings:integrations")

    def form_valid(self, form):
        self.object = self.get_object()

        secret_value = self.kwargs.get("secret")
        if secret_value not in [
            item["id"] for item in self.object.filled_secret_values
        ]:
            raise Http404

        self.object.extra_args.pop(secret_value)
        self.object.save()
        success_url = reverse_lazy("integrations:update-creds", args=[self.object.pk])
        return HttpResponseRedirect(success_url)


class IntegrationOauthRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, pk, *args, **kwargs):
        integration = get_object_or_404(
            Integration,
            pk=pk,
            manifest__oauth__isnull=False,
            enabled_oauth=False,
        )
        return integration._replace_vars(
            integration.manifest["oauth"]["authenticate_url"]
        )


class IntegrationOauthCallbackView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, pk, *args, **kwargs):
        integration = get_object_or_404(
            Integration,
            pk=pk,
            manifest__oauth__isnull=False,
            enabled_oauth=False,
        )
        code = self.request.GET.get("code", "")
        if code == "" and not integration.manifest["oauth"].get("without_code", False):
            messages.error(self.request, "Code was not provided")
            return reverse_lazy("settings:integrations")

        # Check if url has parameters already
        access_obj = integration.manifest["oauth"]["access_token"]
        if not integration.manifest["oauth"].get("without_code", False):
            parsed_url = urlparse(access_obj["url"])
            if len(parsed_url.query):
                access_obj["url"] += "&code=" + code
            else:
                access_obj["url"] += "?code=" + code

        success, response = integration.run_request(access_obj)

        if not success:
            messages.error(self.request, f"Couldn't save token: {response}")
            return reverse_lazy("settings:integrations")

        integration.extra_args["oauth"] = response.json()
        if "expires_in" in response.json():
            integration.expiring = timezone.now() + timedelta(
                seconds=response.json()["expires_in"]
            )

        integration.enabled_oauth = True
        integration.save(update_fields=["enabled_oauth", "extra_args", "expiring"])

        return reverse_lazy("settings:integrations")


class SlackOAuthView(LoginRequiredMixin, View):
    def get(self, request):
        access_token, _dummy = Integration.objects.get_or_create(
            integration=Integration.Type.SLACK_BOT
        )
        if "code" not in request.GET:
            messages.error(
                request,
                _("Could not optain slack authentication code."),
            )
            return redirect("settings:integrations")
        code = request.GET["code"]
        params = {
            "code": code,
            "client_id": access_token.client_id,
            "client_secret": access_token.client_secret,
            "redirect_uri": access_token.redirect_url,
        }
        url = "https://slack.com/api/oauth.v2.access"
        json_response = requests.get(url, params)
        data = json.loads(json_response.text)
        if data["ok"]:
            access_token.bot_token = data["access_token"]
            access_token.bot_id = data["bot_user_id"]
            access_token.token = data["access_token"]
            access_token.save()
            messages.success(
                request,
                _(
                    "Slack has successfully been connected. You have a new bot in your "
                    "workspace."
                ),
            )
        else:
            messages.error(request, _("Could not get tokens from Slack"))
        return redirect("settings:integrations")


class IntegrationTrackerListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    queryset = (
        IntegrationTracker.objects.all()
        .select_related("integration", "for_user")
        .filter(integration__is_active=True)
        .order_by("-ran_at")
    )
    template_name = "tracker_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("All integration runs")
        context["subtitle"] = _("integrations")
        return context


class IntegrationTrackerDetailView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    model = IntegrationTracker
    template_name = "tracker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("%(integration)s for %(user)s") % {
            "integration": (
                self.object.integration.name
                if self.object.integration is not None
                else "Test integration"
            ),
            "user": self.object.for_user,
        }
        context["subtitle"] = _("integrations")
        return context
