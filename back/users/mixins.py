from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminOrManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_or_manager


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class IsAdminOrNewHireManagerMixin(UserPassesTestMixin):
    def test_func(self):
        try:
            new_hire = get_user_model().objects.get(id=self.kwargs.get("pk", -1))
        except get_user_model().DoesNotExist:
            return False
        return self.request.user.is_admin or new_hire.manager == self.request.user
