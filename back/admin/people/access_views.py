from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView
from django.utils import timezone

from admin.integrations.forms import IntegrationExtraUserInfoForm
from admin.integrations.models import Integration
from users.mixins import (
    IsAdminOrNewHireManagerMixin,
    LoginRequiredMixin,
)
from users.models import UserIntegration


class NewHireAccessView(LoginRequiredMixin, IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_access.html"
    model = get_user_model()
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.full_name
        context["subtitle"] = _("new hire")
        context["loading"] = True
        context["integrations"] = Integration.objects.account_provision_options()
        return context


class UserCheckAccessView(LoginRequiredMixin, IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "_user_access_card.html"
    model = get_user_model()
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        found_user = integration.user_exists(self.object)
        context["integration"] = integration
        context["active"] = found_user
        return context


class UserGiveAccessView(LoginRequiredMixin, IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "give_user_access.html"
    model = get_user_model()
    context_object_name = "object"

    def post(self, request, *args, **kwargs):
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = self.get_object()

        # user added access manually, so just log it
        if integration.skip_user_provisioning:
            # this should only very rarely occur
            if UserIntegration.objects.filter(
                user=user, integration=integration, revoked_at__isnull=True
            ).exists():
                return redirect("people:new_hire_access", pk=user.id)

            # create integration if we don't have an open one
            UserIntegration.objects.create(user=user, integration=integration)
            return redirect("people:new_hire_access", pk=user.id)

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

            return redirect("people:new_hire_access", pk=user.id)

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


class UserRevokeAccessView(
    LoginRequiredMixin, IsAdminOrNewHireManagerMixin, DetailView
):
    template_name = "revoke_user_access.html"
    model = get_user_model()
    context_object_name = "object"

    def post(self, request, *args, **kwargs):
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = self.get_object()

        # user added access manually, so just log it being revoked
        if integration.skip_user_provisioning:
            existing_user_integration_log = UserIntegration.objects.filter(
                user=user, integration=integration, revoked_at__isnull=True
            ).first()
            if existing_user_integration_log is not None:
                existing_user_integration_log.revoked_at = timezone.now()
                existing_user_integration_log.save()

            return redirect("people:new_hire_access", pk=user.id)

        success, error = integration.revoke_user(user)

        if success:
            messages.success(request, _("Access has been revoked!"))
        else:
            messages.error(request, _("Access could not be revoked!"))
            messages.error(request, error)

        return redirect("people:new_hire_access", pk=user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = get_object_or_404(
            Integration, id=self.kwargs.get("integration_id", -1)
        )
        user = self.object
        context["integration"] = integration
        context["title"] = user.full_name
        return context
