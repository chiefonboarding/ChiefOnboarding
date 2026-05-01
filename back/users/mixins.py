from django.contrib.auth.mixins import UserPassesTestMixin


class AdminOrManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_or_manager


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin
