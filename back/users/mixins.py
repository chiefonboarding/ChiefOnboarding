from django.contrib.auth.mixins import UserPassesTestMixin

from admin.people.selectors import get_colleagues_for_user, get_new_hires_for_user
from users.models import User


class AdminOrManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_or_manager


class ManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_admin:
            return True

        try:
            get_colleagues_for_user(user=self.request.user).get(
                id=self.kwargs.get("pk", -1)
            )
        except User.DoesNotExist:
            return False

        return True


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class IsAdminOrNewHireManagerMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_admin:
            return True

        try:
            get_new_hires_for_user(user=self.request.user).get(
                id=self.kwargs.get("pk", -1)
            )
        except User.DoesNotExist:
            return False

        return True
