from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views.generic import View


class LoginRedirectView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_admin_or_manager:
            return redirect("admin:new_hires")
        elif request.user.role == get_user_model().Role.NEWHIRE:
            return redirect("new_hire:todos")

        else:
            return redirect("new_hire:colleagues")
