from admin.people.selectors import get_colleagues_for_user, get_new_hires_for_user
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView

from admin.integrations.forms import IntegrationExtraUserInfoForm
from admin.integrations.models import Integration
from users.mixins import AdminOrManagerPermMixin
from users.models import IntegrationUser


class NewHireAccessView(AdminOrManagerPermMixin, DetailView):
    template_name = "new_hire_access.html"

    def get_queryset(self):
        return get_new_hires_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.full_name
        context["subtitle"] = _("new hire")
        context["loading"] = True
        context["integrations"] = Integration.objects.account_provision_options()
        return context


class ColleagueAccessView(AdminOrManagerPermMixin, DetailView):
    template_name = "colleague_access.html"

    def get_queryset(self):
        return get_colleagues_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.full_name
        context["subtitle"] = _("Employee")
        context["loading"] = True
        context["integrations"] = Integration.objects.account_provision_options()
        return context


class UserDeleteView(AdminOrManagerPermMixin, SuccessMessageMixin, DeleteView):
    template_name = "user_delete.html"
    success_url = reverse_lazy("people:new_hires")
    success_message = _("User has been removed")

    def get_queryset(self):
        return get_colleagues_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provision_options = Integration.objects.account_provision_options()
        context["automated_provisioned_items"] = provision_options.exclude(
            manifest_type=Integration.ManifestType.MANUAL_USER_PROVISIONING
        )
        context["manual_provisioned_items"] = IntegrationUser.objects.filter(
            user=self.object, revoked=False
        ).select_related("integration")
        return context

    def form_valid(self, form):
        EmailAddress.objects.filter(user=self.object).delete()
        return super().form_valid(form)


class UserRevokeAllAccessView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_new_hires_for_user(user=self.request.user), id=self.kwargs.get("pk", -1))
        for integration in Integration.objects.filter(
            manifest_type=Integration.ManifestType.WEBHOOK,
            manifest__revoke__isnull=False,
            manifest__exists__isnull=False,
        ):
            if integration.user_exists(user):
                # Any failed attempts will show up as it will refetch all items to
                # check if the accounts have been deleted. So we can safely ignore
                # response here
                integration.revoke_user(user)

        return redirect("people:delete", user.id)


class UserCheckAccessView(AdminOrManagerPermMixin, DetailView):
    template_name = "_user_access_card.html"

    def get_queryset(self):
        return get_colleagues_for_user(user=self.request.user)

    def get_template_names(self):
        if "compact" in self.request.path:
            return ["_user_access_card_compact.html"]
        else:
            return ["_user_access_card.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        found_user = integration.user_exists(self.object)
        context["integration"] = integration
        context["active"] = found_user
        context["needs_user_info"] = integration.needs_user_info(self.object)
        return context


class UserGiveAccessView(AdminOrManagerPermMixin, DetailView):
    template_name = "give_user_access.html"

    def get_queryset(self):
        return get_colleagues_for_user(user=self.request.user)

    def post(self, request, *args, **kwargs):
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = self.get_object()

        integration_config_form = integration.config_form(request.POST)
        user_details_form = IntegrationExtraUserInfoForm(
            data=request.POST,
            instance=user,
            missing_info=integration.manifest.get("extra_user_info", []),
        )

        if integration_config_form.is_valid() and user_details_form.is_valid():
            user.extra_fields |= user_details_form.cleaned_data
            user.save()

            success, error = integration.execute(
                user, integration_config_form.cleaned_data
            )

            if success:
                messages.success(request, _("Account has been created"))
            else:
                messages.error(request, _("Account could not be created"))
                messages.error(request, error)

            if user.role == get_user_model().Role.NEWHIRE:
                return redirect("people:new_hire_access", user.id)
            else:
                return redirect("people:colleague_access", user.id)

        else:
            return render(
                request,
                self.template_name,
                {
                    "integration": integration,
                    "integration_config_form": integration_config_form,
                    "user_details_form": user_details_form,
                    "title": user.full_name,
                },
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = self.object
        context["integration"] = integration
        context["integration_config_form"] = integration.config_form()
        context["user_details_form"] = IntegrationExtraUserInfoForm(
            instance=user,
            missing_info=integration.manifest.get("extra_user_info", []),
        )
        context["title"] = user.full_name
        return context


class UserToggleAccessView(AdminOrManagerPermMixin, View):
    def post(self, request, *args, **kwargs):
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = get_object_or_404(get_new_hires_for_user(user=self.request.user), id=self.kwargs.get("pk", -1))

        # user added/revoked access manually, so just log it being revoked/added
        if integration.skip_user_provisioning:
            # check if exists
            user_integration, created = IntegrationUser.objects.get_or_create(
                user=user, integration=integration
            )
            if not created:
                user_integration.revoked = not user_integration.revoked
                user_integration.save()

            return render(
                request,
                "_user_access_card.html",
                {
                    "object": user,
                    "integration": integration,
                    "active": not user_integration.revoked,
                },
            )

        created = False
        needs_user_info = integration.needs_user_info(user)
        if integration.user_exists(user):
            success, error = integration.revoke_user(user)
            if error:
                created = None
        else:
            success, error = integration.execute(user)
            created = True

        return render(
            request,
            "_user_access_card.html",
            {
                "object": user,
                "integration": integration,
                "active": created,
                "error": error,
                "needs_user_info": needs_user_info,
            },
        )
