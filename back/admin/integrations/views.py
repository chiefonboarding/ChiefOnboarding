import csv
import json
from datetime import timedelta
from urllib.parse import urlencode, urlparse

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django_q.tasks import async_task

from users.mixins import AdminOrManagerPermMixin, AdminPermMixin
from users.models import IntegrationUser

from .forms import IntegrationExtraArgsForm, IntegrationForm
from .models import Integration, IntegrationTracker


class IntegrationCreateView(AdminPermMixin, CreateView, SuccessMessageMixin):
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


class IntegrationUpdateView(AdminPermMixin, UpdateView, SuccessMessageMixin):
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


class IntegrationDeleteView(AdminPermMixin, DeleteView):
    """This is a general delete function for all integrations"""

    template_name = "integration-delete.html"
    model = Integration
    success_url = reverse_lazy("settings:integrations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete integration")
        context["subtitle"] = _("settings")
        return context


class IntegrationUpdateExtraArgsView(AdminPermMixin, UpdateView, SuccessMessageMixin):
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


class IntegrationDeleteExtraArgsView(AdminPermMixin, DeleteView, SuccessMessageMixin):
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


class IntegrationOauthRedirectView(RedirectView):
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


class IntegrationOauthCallbackView(RedirectView):
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


class SlackOAuthView(View):
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


class IntegrationTrackerListView(AdminOrManagerPermMixin, ListView):
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


class IntegrationTrackerDetailView(AdminOrManagerPermMixin, DetailView):
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


class IntegrationBackfillIDsView(AdminPermMixin, View):
    def post(self, request, pk):
        integration = get_object_or_404(Integration, pk=pk)
        if not integration.can_backfill_ids:
            messages.error(
                request,
                _("This integration has no store_data declared on its exists block."),
            )
            return redirect("settings:integrations")
        async_task(
            "admin.integrations.tasks.backfill_integration_ids",
            integration.id,
            task_name=f"Backfill IDs: {integration.name}",
        )
        messages.success(
            request,
            _("Backfill started for %(name)s. Users' extra fields will populate "
              "as the lookup runs in the background.") % {"name": integration.name},
        )
        return redirect("settings:integrations")


STATUS_ACTIVE = "active"
STATUS_REVOKED = "revoked"
STATUS_NONE = "none"

ACCESS_REPORT_PAGE_SIZES = [10, 25, 50, 100]


def _resolve_per_page(value, default):
    try:
        per_page = int(value)
    except (TypeError, ValueError):
        return default
    return per_page if per_page in ACCESS_REPORT_PAGE_SIZES else default


def _filtered_users_queryset(role_filter=None, search=None):
    User = get_user_model()
    users_qs = User.objects.filter(is_active=True).order_by("first_name", "last_name")
    if role_filter == "newhire":
        users_qs = users_qs.filter(role=User.Role.NEWHIRE)
    elif role_filter == "colleague":
        users_qs = users_qs.exclude(role=User.Role.NEWHIRE)
    if search:
        users_qs = users_qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )
    return users_qs


def _build_access_matrix(role_filter=None, search=None, users=None):
    integrations = list(
        Integration.objects.account_provision_options()
        .filter(is_active=True)
        .order_by("name")
    )
    integration_ids = [i.id for i in integrations]

    if users is None:
        users = list(_filtered_users_queryset(role_filter, search))

    user_ids = [u.id for u in users]
    access_lookup = {}
    for iu in IntegrationUser.objects.filter(
        integration_id__in=integration_ids,
        user_id__in=user_ids,
    ).only("user_id", "integration_id", "revoked"):
        access_lookup[(iu.user_id, iu.integration_id)] = (
            STATUS_REVOKED if iu.revoked else STATUS_ACTIVE
        )

    rows = []
    for user in users:
        cells = []
        for integration in integrations:
            cells.append(
                access_lookup.get((user.id, integration.id), STATUS_NONE)
            )
        rows.append({"user": user, "cells": cells})

    return integrations, rows


class IntegrationAccessReportView(AdminOrManagerPermMixin, TemplateView):
    template_name = "access_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_filter = self.request.GET.get("role", "all")
        search = self.request.GET.get("q", "").strip()

        per_page = _resolve_per_page(
            self.request.GET.get("per_page"), settings.ACCESS_REPORT_PAGINATE_BY
        )

        users_qs = _filtered_users_queryset(role_filter=role_filter, search=search)
        paginator = Paginator(users_qs, per_page)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        integrations, rows = _build_access_matrix(
            role_filter=role_filter,
            search=search,
            users=list(page_obj.object_list),
        )

        preserved = {"role": role_filter, "per_page": per_page}
        if search:
            preserved["q"] = search
        context["title"] = _("Integration access report")
        context["subtitle"] = _("reports")
        context["integrations"] = integrations
        context["rows"] = rows
        context["role_filter"] = role_filter
        context["search"] = search
        context["per_page"] = per_page
        context["page_size_options"] = ACCESS_REPORT_PAGE_SIZES
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["preserved_query"] = urlencode(preserved)
        return context


class IntegrationAccessReportRefreshView(AdminPermMixin, View):
    def post(self, request, *args, **kwargs):
        async_task(
            "admin.integrations.tasks.refresh_access_report",
            task_name="Refresh access report",
        )
        messages.success(
            request,
            _(
                "Refreshing access data in the background. The report will update "
                "as each integration finishes its lookups."
            ),
        )
        return redirect("integrations:access-report")


class IntegrationAccessReportCSVView(AdminOrManagerPermMixin, View):
    def get(self, request, *args, **kwargs):
        role_filter = request.GET.get("role", "all")
        search = request.GET.get("q", "").strip()
        integrations, rows = _build_access_matrix(
            role_filter=role_filter, search=search
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="integration-access-report.csv"'
        )
        cell_labels = {
            STATUS_ACTIVE: "Active",
            STATUS_REVOKED: "Not Active",
            STATUS_NONE: "",
        }
        writer = csv.writer(response)
        writer.writerow(
            ["Name", "Email"] + [i.name for i in integrations]
        )
        for row in rows:
            user = row["user"]
            writer.writerow(
                [user.full_name, user.email]
                + [cell_labels[c] for c in row["cells"]]
            )
        return response
