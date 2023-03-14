import requests
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, signals
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.edit import FormView

from admin.integrations.models import Integration
from admin.settings.forms import OTPVerificationForm
from organization.models import Organization
from users.mixins import LoginRequiredMixin as LoginWithMFARequiredMixin


class LoginRedirectView(LoginWithMFARequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_admin_or_manager:
            return redirect("admin:new_hires")
        elif request.user.role == 0:
            return redirect("new_hire:todos")
        else:
            return redirect("new_hire:colleagues")


class AuthenticateView(LoginView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            org = Organization.object.get()
        except Organization.DoesNotExist:
            # there is no org yet, so let's go to the setup page
            return redirect("setup")

        # Block anyone trying to login when credentials are not allowed
        if request.method == "POST" and not org.credentials_login:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = Organization.object.get()
        context["base_url"] = settings.BASE_URL
        if Integration.objects.filter(integration=3, active=True).exists():
            context["google_login"] = Integration.objects.get(
                integration=3, active=True
            )

        return context


@method_decorator(axes_dispatch, name="dispatch")
class MFAView(LoginRequiredMixin, FormView):
    template_name = "mfa.html"
    form_class = OTPVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        # Check if recovery key was entered instead
        recovery_key = self.request.user.check_otp_recovery_key(form.data["otp"])
        if recovery_key is not None:
            self.request.user.requires_otp = False
            self.request.user.save()
            return redirect("logged_in_user_redirect")

        # Log wrong keys by ip to prevent guessing/bruteforcing
        signals.user_login_failed.send(
            sender=self.request.user,
            request=self.request,
            credentials={
                "token": "MFA invalid",
            },
        )
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        self.request.session["passed_mfa"] = True
        return redirect("logged_in_user_redirect")


class GoogleLoginView(View):
    permanent = False

    def dispatch(self, request, *args, **kwargs):
        org = Organization.object.get()
        if not org.google_login:
            raise Http404

        # Make sure access token exists. Technically, it shouldn't be possible
        # to enable `google_login` when this is not set, but just to be safe
        if not Integration.objects.filter(integration=3, active=True).exists():
            return HttpResponse(_("Google login access token has not been set"))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        access_code = Integration.objects.get(integration=3, active=True)
        try:
            r = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": request.GET.get("code", ""),
                    "client_id": access_code.client_id,
                    "client_secret": access_code.client_secret,
                    "redirect_uri": settings.BASE_URL + "/api/auth/google_login",
                    "grant_type": "authorization_code",
                },
            )
            user_access_token = r.json()["access_token"]

            user_info = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo"
                f"?access_token={user_access_token}",
            ).json()
        except Exception:
            messages.error(
                request,
                _("Something went wrong with reaching Google. Please try again."),
            )
            return redirect("login")
        if "email" in user_info:
            users = get_user_model().objects.filter(email=user_info["email"])
            if users.exists():
                user = users.first()
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
                # Also pass MFA, since Google handles that (otherwise they would get
                # stuck in our app having to pass MFA)
                self.request.session["passed_mfa"] = True
                return redirect("logged_in_user_redirect")

        messages.error(
            request,
            _(
                "There is no account associated with your email address. Did you try to"
                " log in with the correct account?"
            ),
        )
        return redirect("login")
