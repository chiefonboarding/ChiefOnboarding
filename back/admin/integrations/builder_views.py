import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, FormView, UpdateView

from admin.integrations.exceptions import (
    DataIsNotJSONError,
    FailedPaginatedResponseError,
    KeyIsNotInDataError,
)
from admin.integrations.models import Integration, IntegrationTracker
from admin.integrations.sync_userinfo import SyncUsers
from users.mixins import AdminPermMixin
from users.models import User

from .builder_forms import (
    ManifestExecuteForm,
    ManifestExistsForm,
    ManifestExtractDataForm,
    ManifestFormForm,
    ManifestHeadersForm,
    ManifestInitialDataForm,
    ManifestOauthForm,
    ManifestRevokeForm,
    ManifestUserInfoForm,
)
from .utils import convert_array_to_object, convert_object_to_array


class SingleObjectMixinWithObj(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)


class RedirectToSelfMixin:
    def get_success_url(self):
        return self.request.path


class IntegrationBuilderCreateView(LoginRequiredMixin, AdminPermMixin, CreateView):
    template_name = "token_create.html"
    model = Integration
    fields = ["name", "manifest_type"]

    def form_valid(self, form):
        form.instance.integration = Integration.Type.CUSTOM
        form.instance.is_active = False
        form.instance.manifest = {"execute": []}
        obj = form.save()
        return HttpResponseRedirect(
            reverse("integrations:builder-detail", args=[obj.id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create new test integration")
        context["subtitle"] = _("integrations")
        return context


class IntegrationBuilderMakeActiveUpdateView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = Integration
    fields = []
    success_url = reverse_lazy("settings:integrations")

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)


class IntegrationBuilderView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "manifest_test.html"
    model = Integration
    context_object_name = "integration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = self.object.manifest
        for form in manifest.get("form", []):
            options_source = form.get("options_source", None)
            if options_source is None:
                if form.get("url", "") == "":
                    form["options_source"] = "fixed list"
                else:
                    form["options_source"] = "fetch url"
        self.object.manifest = manifest
        self.object.save()

        context["form"] = ManifestFormForm()
        context["users"] = User.objects.all()
        context["title"] = _("Integration builder")
        context["subtitle"] = _("integrations")
        if self.object.is_sync_users_integration:
            context["form"] = ManifestHeadersForm(
                initial={
                    "headers": convert_object_to_array(
                        self.object.manifest.get("headers", {})
                    )
                }
            )
        else:
            context["existing_form_items"] = [
                (ManifestFormForm(initial=form, disabled=True), idx)
                for idx, form in enumerate(self.object.manifest.get("form", []))
            ]
        return context


class IntegrationBuilderFormCreateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/form.html"
    model = Integration
    context_object_name = "integration"
    form_class = ManifestFormForm

    def form_valid(self, form):
        manifest = self.object.manifest
        if "form" not in manifest:
            manifest["form"] = []
        manifest["form"].append(form.cleaned_data)
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_form_items"] = [
            (ManifestFormForm(initial=form, disabled=True), idx)
            for idx, form in enumerate(self.object.manifest.get("form", []))
        ]
        return context


class IntegrationBuilderFormUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/_update_form.html"
    model = Integration
    context_object_name = "integration"
    form_class = ManifestFormForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = self.object.manifest["form"][self.kwargs["index"]]
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        data = form.cleaned_data
        if len(data.get("items", [])):
            data["choice_value"] = "key"
            data["choice_name"] = "value"

        if form.cleaned_data.get("options_source") == "fixed list":
            form.cleaned_data["url"] = ""

        manifest["form"][self.kwargs["index"]] = form.cleaned_data
        self.object.manifest = manifest
        self.object.save()
        form = self.form_class(
            initial=self.object.manifest["form"][self.kwargs["index"]], disabled=True
        )
        return render(
            self.request,
            self.template_name,
            {"form": form, "index": self.kwargs["index"], "integration": self.object},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["index"] = self.kwargs["index"]
        return context


class IntegrationBuilderFormDeleteView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        manifest = integration.manifest
        del manifest["form"][self.kwargs["index"]]
        integration.manifest = manifest
        integration.save()
        return HttpResponse()


class IntegrationBuilderHeadersUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    SuccessMessageMixin,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/headers.html"
    form_class = ManifestHeadersForm
    model = Integration
    success_message = _("Headers have been updated")
    context_object_name = "integration"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "headers": convert_object_to_array(self.object.manifest.get("headers", {}))
        }
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest["headers"] = convert_array_to_object(form.cleaned_data["headers"])
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)


class IntegrationBuilderExistsUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    SuccessMessageMixin,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/exists.html"
    form_class = ManifestExistsForm
    model = Integration
    context_object_name = "integration"
    success_message = _("Exists check has been updated")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = self.object.manifest.get("exists", {})
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest["exists"] = form.cleaned_data
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)


class IntegrationBuilderRevokeCreateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/revoke.html"
    form_class = ManifestRevokeForm
    model = Integration
    context_object_name = "integration"

    def form_valid(self, form):
        manifest = self.object.manifest
        if "revoke" not in manifest:
            manifest["revoke"] = []
        manifest["revoke"].append(form.cleaned_data)
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_form_items"] = [
            (ManifestRevokeForm(initial=form, disabled=True), idx)
            for idx, form in enumerate(self.object.manifest.get("revoke", []))
        ]
        return context


class IntegrationBuilderRevokeUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/_update_revoke.html"
    form_class = ManifestRevokeForm
    model = Integration
    context_object_name = "integration"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = self.object.manifest["revoke"][self.kwargs["index"]]
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest["revoke"][self.kwargs["index"]] = form.cleaned_data
        self.object.manifest = manifest
        self.object.save()
        form = self.form_class(
            initial=self.object.manifest["execute"][self.kwargs["index"]], disabled=True
        )
        return render(
            self.request,
            "manifest_test/revoke_disabled_form.html",
            {"form": form, "index": self.kwargs["index"], "integration": self.object},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["index"] = self.kwargs["index"]
        return context


class IntegrationBuilderRevokeDeleteView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        manifest = integration.manifest
        del manifest["revoke"][self.kwargs["index"]]
        integration.manifest = manifest
        integration.save()
        return HttpResponse()


class IntegrationBuilderInitialDataFormCreateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/initial_data_form.html"
    form_class = ManifestInitialDataForm
    success_message = _("Initial data item has been added")
    model = Integration
    context_object_name = "integration"

    def form_valid(self, form):
        manifest = self.object.manifest
        if "initial_data_form" not in manifest:
            manifest["initial_data_form"] = []
        manifest["initial_data_form"].append(form.cleaned_data)
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_form_items"] = [
            (ManifestInitialDataForm(initial=form, disabled=True), idx)
            for idx, form in enumerate(
                self.object.manifest.get("initial_data_form", [])
            )
        ]
        return context


class IntegrationBuilderInitialDataFormDeleteView(
    LoginRequiredMixin, AdminPermMixin, View
):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        manifest = integration.manifest
        # remove value from saved extra args
        try:
            del integration.extra_args[
                manifest["initial_data_form"][self.kwargs["index"]]["id"]
            ]
            integration.save()
        except KeyError:
            pass
        del manifest["initial_data_form"][self.kwargs["index"]]
        integration.manifest = manifest
        integration.save()
        return HttpResponse()


class IntegrationBuilderUserInfoFormCreateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/user_info_form.html"
    form_class = ManifestUserInfoForm
    success_message = _("User info item has been added")
    model = Integration
    context_object_name = "integration"

    def form_valid(self, form):
        manifest = self.object.manifest
        if "extra_user_info" not in manifest:
            manifest["extra_user_info"] = []
        manifest["extra_user_info"].append(form.cleaned_data)
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_form_items"] = [
            (ManifestUserInfoForm(initial=form, disabled=True), idx)
            for idx, form in enumerate(self.object.manifest.get("extra_user_info", []))
        ]
        return context


class IntegrationBuilderUserInfoFormDeleteView(
    LoginRequiredMixin, AdminPermMixin, View
):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        manifest = integration.manifest
        del manifest["extra_user_info"][self.kwargs["index"]]
        integration.manifest = manifest
        integration.save()
        return HttpResponse()


class IntegrationBuilderExecuteCreateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/execute.html"
    form_class = ManifestExecuteForm
    model = Integration
    context_object_name = "integration"

    def form_valid(self, form):
        manifest = self.object.manifest
        if "execute" not in manifest:
            manifest["execute"] = []
        manifest["execute"].append(form.cleaned_data)
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_form_items"] = [
            (ManifestExecuteForm(initial=form, disabled=True), idx)
            for idx, form in enumerate(self.object.manifest.get("execute", []))
        ]
        return context


class IntegrationBuilderExecuteUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    RedirectToSelfMixin,
    SingleObjectMixinWithObj,
    FormView,
):
    template_name = "manifest_test/_update_execute.html"
    form_class = ManifestExecuteForm
    model = Integration
    context_object_name = "integration"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = self.object.manifest["execute"][self.kwargs["index"]]
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest["execute"][self.kwargs["index"]] = form.cleaned_data
        self.object.manifest = manifest
        self.object.save()
        form = self.form_class(
            initial=self.object.manifest["execute"][self.kwargs["index"]], disabled=True
        )
        return render(
            self.request,
            "manifest_test/execute_disabled_form.html",
            {"form": form, "index": self.kwargs["index"], "integration": self.object},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["index"] = self.kwargs["index"]
        return context


class IntegrationBuilderExecuteDeleteView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        manifest = integration.manifest
        del manifest["execute"][self.kwargs["index"]]
        integration.manifest = manifest
        integration.save()
        return HttpResponse()


class IntegrationBuilderTestFormView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        form = integration.config_form()
        return render(self.request, "manifest_test/test_form.html", {"form": form})


class IntegrationBuilderTestView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        test_options = ["exists", "revoke", "execute"]
        test_type = self.kwargs["what"]
        if self.kwargs["what"] not in test_options:
            raise Http404

        integration = get_object_or_404(Integration, id=self.kwargs["pk"])
        extra_fields = json.loads(self.request.POST.get("extra_values", "{}"))

        try:
            user = get_user_model().objects.get(id=self.request.POST.get("user", -1))
            user.extra_fields |= convert_array_to_object(extra_fields)
        except (get_user_model().DoesNotExist, ValueError):
            return render(
                self.request,
                "manifest_test/test_execute.html",
                {"error": "no user selected"},
            )
        if test_type == "exists":
            result = integration.user_exists(user, save_result=False)
        elif test_type == "execute":
            result = integration.execute(user)
        elif test_type == "revoke":
            result = integration.revoke_user(user)

        tracker = IntegrationTracker.objects.filter(
            integration=integration, for_user=user
        ).last()

        return render(
            self.request,
            "manifest_test/test_execute.html",
            {"result": result, "integration": integration, "tracker": tracker},
        )


class IntegrationBuilderSyncTestView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, *args, **kwargs):
        integration = get_object_or_404(Integration, id=self.kwargs["pk"])

        error = None
        users = []
        try:
            # we are passing in the user who is requesting it, but we likely don't need
            # them.
            users = SyncUsers(integration).get_import_user_candidates()
        except (
            KeyIsNotInDataError,
            FailedPaginatedResponseError,
            DataIsNotJSONError,
        ) as e:
            error = e

        tracker = IntegrationTracker.objects.filter(integration=integration).last()

        return render(
            self.request,
            "manifest_test/test_sync.html",
            {
                "integration": integration,
                "tracker": tracker,
                "users": users,
                "error": error,
            },
        )


class IntegrationBuilderOauthUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    SuccessMessageMixin,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/oauth.html"
    form_class = ManifestOauthForm
    model = Integration
    success_message = _("Oauth has been updated")
    context_object_name = "integration"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {"oauth": self.object.manifest.get("oauth", {})}
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest["oauth"] = form.cleaned_data["oauth"]
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)


class IntegrationBuilderExtractDataUpdateView(
    LoginRequiredMixin,
    AdminPermMixin,
    SingleObjectMixinWithObj,
    SuccessMessageMixin,
    RedirectToSelfMixin,
    FormView,
):
    template_name = "manifest_test/extract_data.html"
    form_class = ManifestExtractDataForm
    model = Integration
    success_message = _("Extract data has been updated")
    context_object_name = "integration"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = self.object.manifest
        return kwargs

    def form_valid(self, form):
        manifest = self.object.manifest
        manifest |= form.cleaned_data
        self.object.manifest = manifest
        self.object.save()
        return super().form_valid(form)
