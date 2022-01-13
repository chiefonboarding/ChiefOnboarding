from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login


class LoginRequiredMixin(AccessMixin):
    """
    Verify if user is logged in.
    If user requires mfa, then force it after logging in.
    """

    def dispatch(self, request, *args, **kwargs):
        # Make sure user is logged in
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # If MFA has been enabled, then force it
        if request.user.requires_otp and not request.session.get('passed_mfa', False):
            path = self.request.get_full_path()
            return redirect_to_login(
                path,
                "/mfa/"
            )
        return super().dispatch(request, *args, **kwargs)


class ManagerPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in [1, 2]


class AdminPermMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 1
