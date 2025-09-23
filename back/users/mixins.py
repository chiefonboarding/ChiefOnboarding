from django.contrib.auth.mixins import UserPassesTestMixin

from admin.people.selectors import get_colleagues_for_user, get_new_hires_for_user
from users.models import User


class AdminOrManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_or_manager


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin
