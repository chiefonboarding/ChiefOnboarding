from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from admin.people.forms import AddUsersToSequenceChoiceForm
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


class AddUserToRoleView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
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

    def _render_response(self):
        return render(
            self.request,
            "_departments_list.html",
            {
                "departments": get_available_departments_for_user(
                    user=self.request.user
                ).prefetch_related("roles__users"),
                "is_users_page": True,
            },
        )

    def delete(self, request, **kwargs):
        self.role.users.remove(self.user)
        return self._render_response()

    def post(self, request, **kwargs):
        self.role.users.add(self.user)
        return self._render_response()


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
        return redirect(
            "people:apply_sequence_to_users_in_role",
            sequence=self.sequence.pk,
            role_pk=self.role.pk,
        )

    def post(self, request, **kwargs):
        self.role.sequences.add(self.sequence)
        return redirect(
            "people:apply_sequence_to_users_in_role",
            sequence=self.sequence.pk,
            role_pk=self.role.pk,
        )


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

    def _render_response(self):
        roles = DepartmentRole.objects.filter(department=self.department).values_list(
            "pk", flat=True
        )
        users = User.objects.filter(department_roles__in=roles).distinct()
        form = AddUsersToSequenceChoiceForm(users=users)
        return render(
            self.request,
            "_departments_list_with_sequence_apply_modal.html",
            {
                "departments": get_available_departments_for_user(
                    user=self.request.user
                ).prefetch_related("roles__users"),
                "is_users_page": False,
                "form": form,
                "modal_url": reverse_lazy(
                    "people:apply_sequence_to_users_in_department",
                    args=[self.sequence.pk, self.department.pk],
                ),
            },
        )

    def post(self, request, *args, **kwargs):
        self.department.sequences.add(self.sequence)
        return redirect(
            "people:apply_sequence_to_users_in_department",
            sequence=self.sequence.pk,
            department_pk=self.department.pk,
        )

    def delete(self, request, *args, **kwargs):
        self.department.sequences.remove(self.sequence)
        return self._render_response()


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
