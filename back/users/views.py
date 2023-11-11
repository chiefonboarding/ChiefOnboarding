from allauth.account.views import LoginView, sensitive_post_parameters_m
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View

from organization.models import Organization


class LoginRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_admin_or_manager:
            return redirect("admin:new_hires")
        elif request.user.role == get_user_model().Role.NEWHIRE:
            return redirect("new_hire:todos")
        else:
            return redirect("new_hire:colleagues")


class CustomLoginView(LoginView):
    @sensitive_post_parameters_m
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        org = Organization.object.get()
        if org is None:
            return redirect("setup")

        # Block anyone trying to login when credentials are not allowed
        if request.method == "POST" and not settings.ALLOW_CREDENTIALS_LOGIN:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
