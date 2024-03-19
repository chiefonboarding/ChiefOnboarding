from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.http import Http404, HttpResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from users.mixins import AdminPermMixin
from users.models import User
from django.utils.translation import gettext as _
from .builder_forms import ManifestFormForm, ManifestHeadersForm, ManifestExistsForm, ManifestInitialDataForm, ManifestUserInfoForm, ManifestRevokeForm, ManifestExecuteForm
from django.views.generic.base import RedirectView
from .models import Integration, IntegrationTracker, Manifest, ManifestExecute, ManifestExists, ManifestRevoke, ManifestInitialData, ManifestForm
from users.mixins import AdminPermMixin, LoginRequiredMixin, ManagerPermMixin
from admin.integrations.models import Integration


class IntegrationBuilderCreateView(LoginRequiredMixin, AdminPermMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if pk := self.kwargs.get("pk", False):
            integration = get_object_or_404(Integration, id=pk)
        else:
            exists = ManifestExists.objects.create()
            revoke = ManifestRevoke.objects.create()
            manifest = Manifest.objects.create(exists=exists, revoke=revoke)
            integration = Integration.objects.create(manifest_obj=manifest, manifest_type=Integration.ManifestType.WEBHOOK, integration=Integration.Type.CUSTOM)

        return reverse("integrations:builder", args=[integration.id])


class IntegrationBuilderView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "manifest_test.html"
    model = Integration
    context_object_name = "integration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ManifestFormForm()
        context["users"] = User.objects.all()
        context["title"] = _("Integration builder")
        context["subtitle"] = _("integrations")
        context["existing_form_items"] = [(ManifestFormForm(instance=form, disabled=True), form.index_id) for form in self.object.manifest_obj.form.all()]
        return context


class IntegrationBuilderFormCreateView(
    LoginRequiredMixin, AdminPermMixin, CreateView
):
    template_name = "manifest_test/form.html"
    form_class = ManifestFormForm

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        form.instance.manifest = Integration.objects.get(id=self.kwargs["integration_id"]).manifest_obj
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        context["existing_form_items"] = [(ManifestFormForm(instance=form, disabled=True), form.index_id) for form in integration.manifest_obj.form.all()]
        return context


class IntegrationBuilderFormUpdateView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    template_name = "manifest_test/_update_form.html"
    form_class = ManifestFormForm
    model = ManifestForm

    def get_success_url(self):
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        return reverse("integrations:manifest-form-add", args=[integration.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        return context


class IntegrationBuilderFormDeleteView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = ManifestForm
    fields = []

    def get_success_url(self):
        return self.request.path

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse()


class IntegrationBuilderHeadersUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "manifest_test/headers.html"
    form_class = ManifestHeadersForm
    model = Manifest
    success_message = _("Headers have been updated")

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integration"] = Integration.objects.get(manifest_obj=self.object)
        return context


class IntegrationBuilderExistsUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "manifest_test/exists.html"
    form_class = ManifestExistsForm
    model = ManifestExists
    success_message = _("Exists check has been updated")

    def get_success_url(self):
        return self.request.path

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integration"] = Integration.objects.get(manifest_obj__exists=self.object)
        return context

class IntegrationBuilderRevokeCreateView(
    LoginRequiredMixin, AdminPermMixin, CreateView
):
    template_name = "manifest_test/revoke.html"
    form_class = ManifestRevokeForm

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        form.instance.manifest = Integration.objects.get(id=self.kwargs["integration_id"]).manifest_obj
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        context["existing_form_items"] = [(ManifestRevokeForm(instance=form, disabled=True), form.id) for form in integration.manifest_obj.revoke.all()]
        return context


class IntegrationBuilderRevokeUpdateView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    template_name = "manifest_test/_update_revoke.html"
    form_class = ManifestRevokeForm
    model = ManifestRevoke

    def get_success_url(self):
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        return reverse("integrations:manifest-revoke-add", args=[integration.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        return context


class IntegrationBuilderRevokeDeleteView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = ManifestRevoke
    fields = []

    def get_success_url(self):
        return self.request.path

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse()


class IntegrationBuilderInitialDataFormCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "manifest_test/initial_data_form.html"
    form_class = ManifestInitialDataForm
    model = Manifest
    success_message = _("Initial data item has been added")

    def get_success_url(self):
        return self.request.path


    def form_valid(self, form):
        manifest = Manifest.objects.get(id=self.kwargs["pk"])
        form.instance.manifest = manifest
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.get(id=self.kwargs["pk"])
        context["existing_form_items"] = [(ManifestInitialDataForm(instance=form, disabled=True), form.index_id) for form in manifest.initial_data_form.all()]
        context["integration"] = Integration.objects.get(manifest_obj=manifest)
        return context


class IntegrationBuilderInitialDataFormDeleteView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = ManifestInitialData
    fields = []
    pk_url_kwarg = "initial_data_form_id"

    def get_success_url(self):
        return self.request.path

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        manifest = Manifest.objects.get(id=self.kwargs["pk"])
        if self.object not in manifest.initial_data_form.all():
            # should never be raised, except for the case of a malicious user
            raise Http404

        integration = manifest.integration
        try:
            del integration.extra_args[self.object.id]
            integration.save()
        except KeyError:
            pass
        self.object.delete()
        return HttpResponse()


class IntegrationBuilderUserInfoFormCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "manifest_test/user_info_form.html"
    form_class = ManifestUserInfoForm
    model = Manifest
    success_message = _("User info item has been added")

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        manifest = Manifest.objects.get(id=self.kwargs["pk"])
        form.instance.manifest = manifest
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.get(id=self.kwargs["pk"])
        context["existing_form_items"] = [(ManifestUserInfoForm(instance=form, disabled=True), form.index_id) for form in manifest.extra_user_info.all()]
        context["integration"] = Integration.objects.get(manifest_obj=manifest)
        return context


class IntegrationBuilderUserInfoFormDeleteView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = ManifestInitialData
    fields = []
    pk_url_kwarg = "user_info_form_id"

    def get_success_url(self):
        return self.request.path

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse()


class IntegrationBuilderExecuteCreateView(
    LoginRequiredMixin, AdminPermMixin, CreateView
):
    template_name = "manifest_test/execute.html"
    form_class = ManifestExecuteForm

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        form.instance.manifest = Integration.objects.get(id=self.kwargs["integration_id"]).manifest_obj
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        context["existing_form_items"] = [(ManifestExecuteForm(instance=form, disabled=True), form.id) for form in integration.manifest_obj.execute.all()]
        return context


class IntegrationBuilderExecuteUpdateView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    template_name = "manifest_test/_update_execute.html"
    form_class = ManifestExecuteForm
    model = ManifestExecute

    def get_success_url(self):
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        return reverse("integrations:manifest-execute-add", args=[integration.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = Integration.objects.get(id=self.kwargs["integration_id"])
        context["integration"] = integration
        return context


class IntegrationBuilderExecuteDeleteView(
    LoginRequiredMixin, AdminPermMixin, UpdateView
):
    model = ManifestExecute
    fields = []

    def get_success_url(self):
        return self.request.path

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse()
