import json
from datetime import timedelta
from urllib.parse import urlparse

import requests
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
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
    template_name = "token_create.html"
    form_class = IntegrationExtraArgsForm
    queryset = Integration.objects.filter(integration=Integration.Type.CUSTOM)
    success_message = _("Your config values have been updated!")
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Add new integration")
        context["subtitle"] = _("settings")
        context["button_text"] = _("Update")
        return context


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
            "integration": self.object.integration.name
            if self.object.integration is not None
            else "Test integration",
            "user": self.object.for_user,
        }
        context["subtitle"] = _("integrations")
        return context


class IntegrationBuilderView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "manifest_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if pk := self.kwargs.get("pk", False):
            manifest = get_object_or_404(Integration, id=pk).manifest
            context["object"] = manifest
            if not manifest.get("exists", {}):
                manifest["exists"] = {
                    "url": "",
                    "method": "",
                    "expected": "",
                    "headers": {},
                    "fail_when_4xx_response_code": False,
                }

            if not manifest.get("revoke", False):
                manifest["revoke"] = []

            for base in [
                manifest["exists"],
                manifest,
                *manifest["form"],
                *manifest["revoke"],
                *manifest["execute"],
            ]:
                if base.get("headers", False):
                    base["headers"] = [
                        {"key": key, "value": value}
                        for key, value in base["headers"].items()
                    ]
                else:
                    base["headers"] = []

            for form in manifest["form"]:
                form["results_from"] = (
                    "fixed" if len(form.get("items", [])) > 0 else "fetched"
                )

            for ex in [*manifest["revoke"], *manifest["execute"]]:
                if ex.get("data", False):
                    ex["data"] = json.dumps(ex["data"])
                else:
                    ex["data"] = "{}"

            context["manifest"] = manifest
            if manifest.get("extra_user_info", False):
                manifest["extra_user_info"] = []
            if manifest.get("initial_data_form", False):
                manifest["extra_user_info"] = []

        context["title"] = _(
            "BETA: Create and test an integration (experimental feature)"
        )
        context["subtitle"] = _("integrations")
        context["users"] = get_user_model().objects.all()
        return context


class IntegrationTestView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request, *args, **kwargs):
        test_type = request.POST.get("type", "form")
        try:
            manifest = json.loads(request.POST.get("manifest", "{}"))
        except ValueError:
            manifest = {}
        try:
            extra_fields = json.loads(request.POST.get("extra_fields", "{}"))
        except ValueError:
            extra_fields = {}
        try:
            extra_args = json.loads(request.POST.get("extra_args", "{}"))
        except ValueError:
            extra_args = {}

        try:
            user = get_user_model().objects.get(id=request.POST.get("user", -1))
        except get_user_model().DoesNotExist:
            return HttpResponse("No user selected")

        for base in [manifest["exists"], manifest, *manifest["form"]]:
            if "headers" in base:
                if base["headers"] == []:
                    del base["headers"]
                    continue
                base["headers"] = {
                    item["key"]: item["value"] for item in base["headers"]
                }

        for idx, ex in enumerate(manifest["execute"]):
            try:
                ex["data"] = json.loads(ex["data"])
            except ValueError:
                return HttpResponse(f"Data of request {idx + 1} is not a valid json")

        extra_args_dict = {item["key"]: item["value"] for item in extra_args}

        try:
            extra_args_dict |= Integration.objects.get(
                id=request.POST.get("integration_id", -1)
            ).extra_args
        except Integration.DoesNotExist:
            # don't use args from original manifest
            pass

        # mock extra fields to user. DO NOT SAVE!
        extra_fields_dict = {item["key"]: item["value"] for item in extra_fields}
        user.extra_fields = extra_fields_dict
        integration = Integration(manifest=manifest, extra_args=extra_args_dict)

        if test_type == "form":
            form = integration.config_form()
            return render(request, "_item_form.html", {"form": form})

        if test_type == "user_exists":
            return HttpResponse(integration.test_user_exists(user))

        if test_type == "execute" or test_type == "revoke":
            if test_type == "execute":
                succeeded, response = integration.execute(user)
            else:
                succeeded, response = integration.revoke_user(user)

            integration_status = "Succeeded" if succeeded else "Failed"

            url = reverse("integrations:tracker", args=[integration.tracker.id])
            return HttpResponse(
                f"{integration_status}\n\n"
                f"<a target='_blank' href='{url}'>See steps here</a>"
            )

        else:
            return HttpResponse("Unknown type")


class IntegrationTestDownloadJSONView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            manifest = json.loads(request.POST.get("manifest", "{}"))
        except ValueError:
            manifest = {}

        for base in [
            manifest["exists"],
            manifest,
            *manifest["form"],
            *manifest["execute"],
        ]:
            if "headers" in base:
                if base["headers"] == []:
                    del base["headers"]
                    continue
                base["headers"] = {
                    item["key"]: item["value"] for item in base["headers"]
                }

        for ex in manifest["execute"]:
            ex["data"] = json.loads(ex["data"])

        if manifest["exists"]["url"] == "":
            del manifest["exists"]

        for item in ["revoke", "extra_user_info", "initial_data_form"]:
            if manifest[item] == []:
                del manifest[item]

        for form_item in manifest["form"]:
            del form_item["results_from"]

        return HttpResponse("<pre>" + json.dumps(manifest, indent=4) + "</pre>")
