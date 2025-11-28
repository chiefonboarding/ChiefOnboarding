from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views.generic import View


class LoginRedirectView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_admin_or_manager:
            return redirect("admin:new_hires")
        else:
            return redirect("new_hire:todos")
