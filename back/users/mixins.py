from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404


class ManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_or_manager


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class IsAdminOrNewHireManagerMixin(UserPassesTestMixin):
    def test_func(self):
        new_hire = get_object_or_404(get_user_model(), id=self.kwargs.get("pk", -1))
        return self.request.user.is_admin or new_hire.manager == self.request.user
