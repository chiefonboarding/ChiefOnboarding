from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from admin.people.forms import (
    AddSequencesToUser,
    AddUsersToSequenceChoiceForm,
    ItemsToBeRemovedForm,
)
from admin.sequences.models import IntegrationConfig
from admin.sequences.selectors import (
    get_onboarding_sequences_for_user,
    get_sequences_for_user,
)
from users.mixins import AdminOrManagerPermMixin
from users.models import Department, DepartmentRole, User
from users.selectors import (
    get_all_users_for_departments_of_user,
    get_available_departments_for_user,
    get_available_roles_for_user,
)


class DepartmentListView(AdminOrManagerPermMixin, ListView):
    template_name = "departments.html"
    context_object_name = "departments"

    def get_queryset(self):
        return get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Roles and departments")
        context["subtitle"] = _("people")
        context["users_or_sequences"] = get_all_users_for_departments_of_user(
            user=self.request.user
        )
        context["is_users_page"] = True
        return context


class DepartmentSequenceListView(AdminOrManagerPermMixin, ListView):
    template_name = "departments.html"
    context_object_name = "departments"

    def get_queryset(self):
        return get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Roles and departments")
        context["subtitle"] = _("sequences")
        context["users_or_sequences"] = get_onboarding_sequences_for_user(
            user=self.request.user
        )
        context["is_users_page"] = False
        return context


class DepartmentCreateView(AdminOrManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "department_create.html"
    model = Department
    fields = [
        "name",
    ]
    success_message = _("Department has been created")
    success_url = reverse_lazy("people:departments")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_manager:
            self.request.user.departments.add(self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Roles and departments")
        context["subtitle"] = _("people")
        return context


class DepartmentUpdateView(AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView):
    template_name = "department_update.html"
    fields = [
        "name",
    ]
    success_message = _("Department has been updated")
    success_url = reverse_lazy("people:departments")

    def get_queryset(self):
        return get_available_departments_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Department")
        context["subtitle"] = _("people")
        return context


class DepartmentRoleCreateView(
    AdminOrManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "role_form.html"
    model = DepartmentRole
    fields = [
        "name",
    ]
    success_message = _("Role has been created")
    success_url = reverse_lazy("people:departments")

    def dispatch(self, *args, **kwargs):
        self.department = get_object_or_404(
            get_available_departments_for_user(user=self.request.user),
            id=self.kwargs.get("pk"),
        )
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.department = self.department
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Roles")
        context["subtitle"] = _("people")
        return context


class DepartmentRoleUpdateView(
    AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "role_form.html"
    fields = [
        "name",
    ]
    success_message = _("Role has been updated")
    success_url = reverse_lazy("people:departments")

    def get_queryset(self):
        return get_available_roles_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Role")
        context["subtitle"] = _("people")
        return context


class ToggleUserToRoleView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
    def dispatch(self, *args, **kwargs):
        self.role = get_object_or_404(
            get_available_roles_for_user(user=self.request.user),
            id=self.kwargs.get("role_pk", -1),
        )
        self.user = get_object_or_404(
            get_all_users_for_departments_of_user(user=self.request.user),
            id=self.request.GET.get("item", -1),
        )
        return super().dispatch(*args, **kwargs)

    def delete(self, request, **kwargs):
        self.role.users.remove(self.user)
        return HttpResponseRedirect(
            reverse_lazy(
                "people:remove_items_from_user", args=[self.role.pk, self.user.pk]
            ),
            status=303,
        )

    def post(self, request, **kwargs):
        self.role.users.add(self.user)
        return redirect(
            "people:apply_sequences_to_user",
            user_pk=self.user.pk,
            role_pk=self.role.pk,
        )


class ToggleSequenceRoleView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
    def dispatch(self, *args, **kwargs):
        self.role = get_object_or_404(
            get_available_roles_for_user(user=self.request.user),
            id=self.kwargs.get("role_pk", -1),
        )
        self.sequence = get_object_or_404(
            get_sequences_for_user(user=self.request.user),
            id=self.request.GET.get("item", -1),
        )
        return super().dispatch(*args, **kwargs)

    def delete(self, request, **kwargs):
        self.role.sequences.remove(self.sequence)
        return HttpResponseRedirect(
            reverse_lazy(
                "people:apply_sequence_to_users_in_role",
                args=[self.sequence.pk, self.role.pk],
            ),
            status=303,
        )

    def post(self, request, **kwargs):
        self.role.sequences.add(self.sequence)
        return redirect(
            "people:apply_sequence_to_users_in_role",
            sequence=self.sequence.pk,
            role_pk=self.role.pk,
        )


class ApplySequencesToUserView(AdminOrManagerPermMixin, SuccessMessageMixin, FormView):
    form_class = AddSequencesToUser
    template_name = "_departments_list_with_sequences_to_user_modal.html"

    def dispatch(self, *args, **kwargs):
        self.role = get_object_or_404(
            get_available_roles_for_user(user=self.request.user),
            id=self.kwargs.get("role_pk"),
        )
        self.user = get_object_or_404(
            get_all_users_for_departments_of_user(user=self.request.user),
            id=self.kwargs.get("user_pk"),
        )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        sequence_pks = list(
            self.role.sequences.all().values_list("pk", flat=True)
        ) + list(self.role.department.sequences.all().values_list("pk", flat=True))
        kwargs["sequence_pks"] = sequence_pks
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")
        context["role"] = self.role
        context["is_users_page"] = True
        context["modal_url"] = reverse_lazy(
            "people:apply_sequences_to_user", args=[self.role.pk, self.user.pk]
        )
        return context

    def form_valid(self, form):
        sequences = form.cleaned_data["sequences"]
        self.user.add_sequences(sequences)
        return HttpResponse(headers={"HX-Trigger": "hide-modal"})


class ToggleSequenceDepartmentView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
    def dispatch(self, *args, **kwargs):
        self.department = get_object_or_404(
            get_available_departments_for_user(user=self.request.user),
            id=self.kwargs.get("department_pk", -1),
        )
        self.sequence = get_object_or_404(
            get_sequences_for_user(user=self.request.user),
            id=self.request.GET.get("item", -1),
        )
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.department.sequences.add(self.sequence)
        return redirect(
            "people:apply_sequence_to_users_in_department",
            sequence=self.sequence.pk,
            department_pk=self.department.pk,
        )

    def delete(self, request, *args, **kwargs):
        self.department.sequences.remove(self.sequence)
        return HttpResponseRedirect(
            reverse_lazy("people:departments_sequences"),
            status=303,
        )


class BaseApplySequenceToUsersView(
    AdminOrManagerPermMixin, SuccessMessageMixin, FormView
):
    form_class = AddUsersToSequenceChoiceForm
    template_name = "_departments_list_with_sequence_apply_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")
        context["is_users_page"] = False
        context["role"] = self.role
        context["department"] = self.department
        context["sequence"] = self.sequence
        context["modal_url"] = self.modal_url
        return context

    def form_valid(self, form):
        users = form.cleaned_data["users"]
        for user in users:
            user.add_sequences([self.sequence])
        return HttpResponse(headers={"HX-Trigger": "hide-modal"})


class ApplySequenceToUsersRoleView(BaseApplySequenceToUsersView):
    def dispatch(self, *args, **kwargs):
        self.sequence = get_object_or_404(
            get_sequences_for_user(user=self.request.user),
            id=self.kwargs.get("sequence"),
        )
        self.role = get_object_or_404(
            get_available_roles_for_user(user=self.request.user),
            id=self.kwargs.get("role_pk"),
        )
        self.department = None
        self.modal_url = reverse_lazy(
            "people:apply_sequence_to_users_in_role",
            args=[self.sequence.pk, self.role.pk],
        )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["users"] = self.role.users.all()
        return kwargs


class ApplySequenceToUsersDepartmentView(BaseApplySequenceToUsersView):
    def dispatch(self, *args, **kwargs):
        self.sequence = get_object_or_404(
            get_sequences_for_user(user=self.request.user),
            id=self.kwargs.get("sequence"),
        )
        self.department = get_object_or_404(
            get_available_departments_for_user(user=self.request.user),
            id=self.kwargs.get("department_pk"),
        )
        self.role = None
        self.modal_url = reverse_lazy(
            "people:apply_sequence_to_users_in_department",
            args=[self.sequence.pk, self.department.pk],
        )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        roles = DepartmentRole.objects.filter(department=self.department).values_list(
            "pk", flat=True
        )
        kwargs["users"] = User.objects.filter(department_roles__in=roles).distinct()
        return kwargs


class RemoveItemsFromUserView(AdminOrManagerPermMixin, SuccessMessageMixin, FormView):
    form_class = ItemsToBeRemovedForm
    template_name = "_departments_list_with_remove_user_options_modal.html"

    def dispatch(self, *args, **kwargs):
        self.role = get_object_or_404(
            get_available_roles_for_user(user=self.request.user),
            id=self.kwargs.get("role_pk"),
        )
        self.user = get_object_or_404(
            get_all_users_for_departments_of_user(user=self.request.user),
            id=self.kwargs.get("user_pk"),
        )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        integration_items = IntegrationConfig.objects.none()
        for seq in (
            self.role.sequences.all() | self.role.department.sequences.all()
        ).prefetch_related("conditions__integration_configs__integration"):
            for con in seq.conditions.all():
                integration_items |= con.integration_configs.filter(
                    integration__manifest__revoke__isnull=False
                )
        kwargs["items"] = integration_items
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departments"] = get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")
        context["modal_url"] = reverse_lazy(
            "people:apply_sequences_to_user", args=[self.role.pk, self.user.pk]
        )
        context["is_users_page"] = True
        return context

    def form_valid(self, form):
        items = form.cleaned_data["items"]
        for integrationconfig in items:
            # TODO: error handling
            integrationconfig.revoke_user(self.user)
        return HttpResponse(headers={"HX-Trigger": "hide-modal"})
