import logging
import re
import uuid

import jwt
import requests
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, signals
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.edit import FormView

from admin.admin_onboarding.utils import check_admin_first_login
from admin.integrations.models import Integration
from admin.settings.forms import OTPVerificationForm
from organization.models import Organization
from users.mixins import LoginRequiredMixin as LoginWithMFARequiredMixin

logger = logging.getLogger(__name__)


class LoginRedirectView(LoginWithMFARequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Check if this is an admin's first login
        if request.user.is_admin:
            # If this is the admin's first login, set up onboarding
            check_admin_first_login(request.user)

        if request.user.is_admin_or_manager:
            # Check if this is a new manager that needs onboarding
            if request.user.role == get_user_model().Role.MANAGER:
                # Check if the manager has any sequences assigned
                if not request.user.sequences.exists():
                    # Assign manager onboarding sequences
                    from admin.sequences.models import Sequence
                    manager_sequences = Sequence.objects.filter(
                        manager_sequence=True,
                        active=True
                    )
                    for sequence in manager_sequences:
                        request.user.add_sequence(sequence)

            return redirect("admin:new_hires")
        elif request.user.role == get_user_model().Role.NEWHIRE:
            return redirect("new_hire:todos")
        else:
            return redirect("new_hire:colleagues")


class AuthenticateView(LoginView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        # add login type to session that can be used in the logout
        self.request.session["login_type"] = ""
        org = Organization.object.get()
        if org is None:
            return redirect("setup")

        # redirect user if they are already logged in
        if request.user.is_authenticated:
            return redirect("logged_in_user_redirect")

        # redirect visitor to OIDC if this has been forced and `disable_force` is
        # not in the url as a query parameter
        if self.request.session.get(
            "force_auth", settings.OIDC_FORCE_AUTHN
        ) and not self.request.GET.get("disable_force", False):
            return redirect("oidc_login")

        # Block anyone trying to login when credentials are not allowed
        if request.method == "POST" and not org.credentials_login:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = Organization.object.get()
        context["base_url"] = settings.BASE_URL
        if Integration.objects.filter(
            integration=Integration.Type.GOOGLE_LOGIN, active=True
        ).exists():
            context["google_login"] = Integration.objects.get(
                integration=Integration.Type.GOOGLE_LOGIN, active=True
            )
        if Organization.object.get().oidc_login:
            context["oidc_display"] = settings.OIDC_LOGIN_DISPLAY
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
        if not Integration.objects.filter(
            integration=Integration.Type.GOOGLE_LOGIN, active=True
        ).exists():
            return HttpResponse(_("Google login access token has not been set"))

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        access_code = Integration.objects.get(
            integration=Integration.Type.GOOGLE_LOGIN, active=True
        )
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


class OIDCLoginView(View):
    permanent = False

    @property
    def redirect_url(self):
        return settings.BASE_URL + reverse("oidc_login")

    def dispatch(self, request, *args, **kwargs):
        # Check if OIDC is enabled
        oidc_login = Organization.object.get().oidc_login
        if not oidc_login:
            self.request.session["force_auth"] = False
            messages.error(
                self.request,
                _("OIDC login has not been enabled."),
            )
            return redirect("login")
        # Make sure these configd exists. Technically, it shouldn't be possible
        # to enable `oidc_login` when this is not set, but just to be safe
        OIDC_CLIENT_ID_VALID = settings.OIDC_CLIENT_ID.strip() != ""
        OIDC_CLIENT_SECRET_VALID = settings.OIDC_CLIENT_SECRET.strip() != ""
        OIDC_AUTHORIZATION_URL_VALID = settings.OIDC_AUTHORIZATION_URL.strip() != ""
        OIDC_TOKEN_URL_VALID = settings.OIDC_TOKEN_URL.strip() != ""
        OIDC_USERINFO_URL_VALID = settings.OIDC_USERINFO_URL.strip() != ""
        is_oidc_config_valid = (
            OIDC_CLIENT_ID_VALID
            and OIDC_CLIENT_SECRET_VALID
            and OIDC_AUTHORIZATION_URL_VALID
            and OIDC_TOKEN_URL_VALID
            and OIDC_USERINFO_URL_VALID
        )
        if not is_oidc_config_valid:
            return HttpResponse(_("OIDC login has not been set"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # If the request contains an authorization code, handle the callback
        authorization_code = request.GET.get("code")
        if authorization_code:
            return self.handle_callback(request, authorization_code)

        # Otherwise, generate the authorization URL and redirect the user to the OIDC
        # provider
        auth_url = self.generate_auth_url()
        return HttpResponseRedirect(auth_url)

    def generate_auth_url(self):
        params = {
            "client_id": settings.OIDC_CLIENT_ID,
            "response_type": "code",
            "scope": settings.OIDC_SCOPES,
            "redirect_uri": self.redirect_url,
        }
        auth_url = (
            settings.OIDC_AUTHORIZATION_URL + "?" + requests.compat.urlencode(params)
        )
        return auth_url

    def handle_callback(self, request, authorization_code):
        try:
            tokens = self.request_tokens(authorization_code)
            access_token = tokens["access_token"]
            request.session["id_token"] = tokens["id_token"]
            user_info = self.get_user_info(access_token)
            user = self.authenticate_user(user_info)
            if user is None:
                request.session["force_auth"] = False
                messages.error(
                    self.request,
                    _(
                        "Cannot get your email address. Did you try to"
                        " log in with the correct account?"
                    ),
                )
                return redirect("login")

            login(request, user)
            # add login type to session, so we can redirect to the correct page when we
            # logout
            self.request.session["login_type"] = "oidc"
            # Also pass MFA, since OIDC handles that (otherwise they would get
            # stuck in our app having to pass MFA)
            self.request.session["passed_mfa"] = True
            return redirect("logged_in_user_redirect")
        except Exception as e:
            logger.error(e)
            self.request.session["force_auth"] = False
            messages.error(
                request,
                _("Something went wrong with reaching OIDC. Please try again."),
            )
            return redirect("login")

    def request_tokens(self, authorization_code):
        data = {
            "client_id": settings.OIDC_CLIENT_ID,
            "client_secret": settings.OIDC_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_url,
        }
        response = requests.post(settings.OIDC_TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(settings.OIDC_USERINFO_URL, headers=headers)
        return response.json()

    def authenticate_user(self, user_info):
        if "email" in user_info:
            user, created = get_user_model().objects.get_or_create(
                email=user_info["email"].lower()
            )
            if created:
                user = self.__sync_user(user_info)
                user.set_unusable_password()
                user.save()
            else:
                user = self.__create_user(user_info)
            user.backend = "django.contrib.auth.backends.ModelBackend"
            return user

    def __create_user(self, user_info):
        user = self.__sync_user(user_info)
        if "name" in user_info:
            name = user_info["name"].split(" ")
            size = len(name)
            if size == 0:
                first_name = "user"
                second_name = ""
            elif len(name) == 1:
                first_name = name[0]
                second_name = ""
            else:
                first_name = name[0]
                second_name = name[1]
            user.first_name = first_name
            user.last_name = second_name
        user.save()
        return user

    def __sync_user(self, user_info):
        user = get_user_model().objects.get(email=user_info["email"])
        if settings.OIDC_ROLE_UPDATING:
            role = self.__check_role(user_info)
            user.role = role
            user.save()
        return user

    def __check_role(self, user_info):
        oidc_roles = self.__get_oidc_roles(user_info)
        if len(oidc_roles) == 0:
            logger.info("ODIC: couldn't find roles in user info, fallback to ID Token")
            claim_roles = self.__extract_claims_from_id_token()
            if claim_roles:
                oidc_roles = self.__get_oidc_roles(claim_roles)
                if len(oidc_roles) == 0:
                    return settings.OIDC_ROLE_DEFAULT
            else:
                return settings.OIDC_ROLE_DEFAULT
        return self.__analyze_role(oidc_roles)

    def __get_oidc_roles(self, json_info):
        tmp = json_info
        for path in settings.OIDC_ROLE_PATH_IN_RETURN:
            path = path.strip(".")
            if path == "":
                continue
            try:
                tmp = tmp[path]
            except KeyError:
                logger.info("OIDC: Path does not exist in the given json")
                return []
        if isinstance(tmp, list):
            return tmp
        elif isinstance(tmp, str):
            return [tmp]
        else:
            return []

    def __extract_claims_from_id_token(self):
        id_token = self.request.session["id_token"]
        if not id_token:
            logger.info("OIDC: could not find ID Token to extract claims")
            return {}

        try:
            claims = jwt.decode(id_token, options={"verify_signature": False})
            return claims
        except Exception as e:
            logger.error(e)
            return {}

    def __analyze_role(self, oidc_roles):
        ROLE_NEW_HIRE_NAME = "newhire"
        ROLE_ADMIN_NAME = "admin"
        ROLE_MANAGER_NAME = "manager"
        role_map = {
            ROLE_NEW_HIRE_NAME: settings.OIDC_ROLE_NEW_HIRE_PATTERN,
            ROLE_ADMIN_NAME: settings.OIDC_ROLE_ADMIN_PATTERN,
            ROLE_MANAGER_NAME: settings.OIDC_ROLE_MANAGER_PATTERN,
        }
        roles = []
        for key in role_map.keys():
            role_name = role_map[key]
            role_name = rf"{role_name}"
            if role_name.strip() == "":
                continue
            for oidc_role in oidc_roles:
                if re.search(role_name, oidc_role):
                    roles.append(key)
        if ROLE_ADMIN_NAME in roles:
            return 1
        elif ROLE_MANAGER_NAME in roles:
            return 2
        elif ROLE_NEW_HIRE_NAME in roles:
            return 0
        else:
            return settings.OIDC_ROLE_DEFAULT


class LogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        logout_state = request.GET.get("state", False)
        if logout_state and logout_state == self.request.session.get(
            "logout_uuid", False
        ):
            # we have logged out of the OIDC, now reset to follow normal logout of
            # Django
            request.session.pop("login_type")
            request.session.pop("id_token")
            request.session.pop("logout_uuid")

        # first logout of OIDC, then return back to follow normal Django logout
        is_oidc_login = request.session.get("login_type", "") == "oidc"
        if settings.OIDC_LOGOUT_URL != "" and is_oidc_login:
            id_token_hint = request.session.get("id_token")
            # upon redirect to Django add state token to check if have indeed logged
            # out of OIDC
            state = str(uuid.uuid4())
            request.session["logout_uuid"] = state
            url = (
                settings.OIDC_LOGOUT_URL
                + f"?id_token_hint={id_token_hint}&state={state}"
                + "&post_logout_redirect_uri="
                + settings.BASE_URL
                + reverse("logout")
            )
            return redirect(url)

        return super().dispatch(request, *args, **kwargs)
