from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminOrManagerPermMixin
from users.models import Department, Role
from users.selectors import (
    get_all_users_for_departments_of_user,
    get_available_departments_for_user,
    get_available_roles_for_user,
)


class DepartmentListView(AdminOrManagerPermMixin, ListView):
    template_name = "departments.html"
    paginate_by = 20
    context_object_name = "departments"

    def get_queryset(self):
        return get_available_departments_for_user(
            user=self.request.user
        ).prefetch_related("roles__users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Roles and departments")
        context["subtitle"] = _("people")
        context["users"] = get_all_users_for_departments_of_user(user=self.request.user)
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


class DepartmentRoleCreateView(
    AdminOrManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "role_create.html"
    model = Role
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


class AddUserToRoleView(AdminOrManagerPermMixin, SuccessMessageMixin, View):
    def post(self, request, role_pk, user_pk, **kwargs):
        role = get_object_or_404(
            get_available_roles_for_user(user=request.user), id=role_pk
        )
        user = get_object_or_404(
            get_all_users_for_departments_of_user(user=request.user), id=user_pk
        )

        role.users.add(user)
        return render(
            request,
            "_departments_list.html",
            {"departments": get_available_departments_for_user(user=self.request.user).prefetch_related("roles__users")},
        )


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


class DepartmentRoleUpdateView(
    AdminOrManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "role_update.html"
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
