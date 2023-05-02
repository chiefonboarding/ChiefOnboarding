import requests
import re
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, signals
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView,LogoutView
from django.http import Http404, HttpResponse,HttpResponse, HttpResponseRedirect
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
        org = Organization.object.get()
        if org is None:
            return redirect("setup")
        if settings.OIDC_FORCE_AUTHN:
            return redirect("oidc_login")

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


class OIDCLoginView(View):
    permanent = False

    def dispatch(self, request, *args, **kwargs):
        # org = Organization.object.get()
        # if not org.oidc_login:
        #     raise Http404
        # OIDC_INTEGRATION_ID=self.INTEGRATION_ID
        # Make sure access token exists. Technically, it shouldn't be possible
        # to enable `oidc_login` when this is not set, but just to be safe
        self.__init_config()
        if not self.ENABLE:
            return HttpResponse(_("OIDC login has not been set"))
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        # If the request contains an authorization code, handle the callback
        # self.__init_config()
        authorization_code = request.GET.get("code")
        if authorization_code:
            return self.handle_callback(request, authorization_code)

        # Otherwise, generate the authorization URL and redirect the user to the OIDC provider
        auth_url = self.generate_auth_url()
        return HttpResponseRedirect(auth_url)

    def generate_auth_url(self):
        params = {
            "client_id": self.CLIENT_ID,
            "response_type": "code",
            "scope": self.SCOPES,
            "redirect_uri": self.REDIRECT_URI,
        }
        auth_url = self.AUTHORIZATION_URL + "?" + requests.compat.urlencode(params)
        return auth_url

    def handle_callback(self, request, authorization_code):
        tokens = self.request_tokens(authorization_code)
        access_token = tokens["access_token"]
        user_info = self.get_user_info(access_token)
        user=self.authenticate_user(user_info)
        login(request, user)
        # Also pass MFA, since Google handles that (otherwise they would get
        # stuck in our app having to pass MFA)
        self.request.session["passed_mfa"] = True
        return redirect("logged_in_user_redirect")
    def request_tokens(self, authorization_code):
        data = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.REDIRECT_URI,
        }
        response = requests.post(self.TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USERINFO_URL, headers=headers)
        return response.json()

    def authenticate_user(self, user_info):
        if self.DEBUG:
            print(user_info)
        User = get_user_model()
        user, created = User.objects.get_or_create(email=user_info["email"])
        if "email" in user_info:
            email = user_info["email"]
            if created:
                user=self.__sync_user(user_info)
            else:
                user=self.__create_user(user_info)
            user.backend = "django.contrib.auth.backends.ModelBackend"
            return user
        messages.error(
            request,
            _(
                "There is no account associated with your email address. Did you try to"
                " log in with the correct account?"
            ),
        )
        return redirect("login")
    
    def __init_config(self):
        self.__load_config_from_settings()
        # OIDC_INTEGRATION_ID=self.INTEGRATION_ID
        # OIDC_INFO = Integration.objects.get(integration=OIDC_INTEGRATION_ID, active=True)
        # self.CLIENT_ID = OIDC_INFO.client_id
        # self.CLIENT_SECRET = OIDC_INFO.client_secret
        # self.REDIRECT_URI = settings.BASE_URL + "/api/auth/oidc_login/"
        # self.AUTHORIZATION_URL = OIDC_INFO.auth_url
        # self.TOKEN_URL = OIDC_INFO.access_token
        # self.USERINFO_URL = OIDC_INFO.user_profile
        # self.SCOPES = "openid email profile"
        # self.PERMISSION_MAP = {"admin": "^cn=Administrators.*", "manage": "^cn=PhD.*"}
        # self.PERMISSION_ADMIN_NAME = "admin"
        # self.PERMISSION_MANAGE_NAME = "manage"
        # self.OIDC_GROUPS_PATH = ["zoneinfo"]
        # self.DEFAULT_ROLE = 3
    
    def __create_user(self,user_info):
        user=self.__sync_user(user_info)
        name=user_info["name"].split(" ")
        size=len(name)
        if size==0:
            first_name = "user"
            second_name = ""
        elif len(name)==1:
            first_name = name[0]
            second_name = ""
        else:
            first_name = name[0]
            second_name = name[1]   
        user.first_name = first_name
        user.last_name = second_name
        user.save()
        return user
    
    def __sync_user(self,user_info):
        permissions = self.__check_permission(user_info)
        email=user_info["email"]
        users = get_user_model().objects.filter(email=user_info["email"])
        user=users.first()
        user.role = permissions
        user.save()
        return user
    
    def __check_permission(self,user_info):
        groups=self.__get_oidc_groups(user_info)
        if len(groups)==0:
            return 3
        return self.__analyze_permission(groups)
        
    def __get_oidc_groups(self,user_info):
        tmp=user_info
        for path in self.OIDC_GROUPS_PATH:
            path=path.strip()
            if path=="":
                continue
            try:
                tmp=tmp[path]
            except:
                return []
        # print(tmp)
        if isinstance(tmp,list):
            return tmp
        elif isinstance(tmp,str):
            return [tmp]
        else:
            return []
    
    def __analyze_permission(self,oidc_groups):
        permission_map=self.PERMISSION_MAP
        if not isinstance(permission_map,dict) or len(oidc_groups)==0:
            return 3
        permissions = []
        for key in permission_map.keys():
            map_value = permission_map[key]
            map_value = rf"{map_value}"
            if map_value.strip() == "":
                continue
            for group in oidc_groups:
                if re.search(map_value, group):
                    permissions.append(key)
                    break
        if self.PERMISSION_ADMIN_NAME in permissions:
            return 1
        elif self.PERMISSION_MANAGE_NAME in permissions:
            return 2
        else:
            return self.DEFAULT_ROLE
        
        
    def __load_config_from_settings(self):
        self.CLIENT_ID = settings.OIDC_CLIENT_ID
        self.CLIENT_SECRET = settings.OIDC_CLIENT_SECRET
        self.REDIRECT_URI = settings.BASE_URL + "/api/auth/oidc_login/"
        self.AUTHORIZATION_URL = settings.OIDC_AUTHORIZATION_URL
        self.TOKEN_URL = settings.OIDC_TOKEN_URL
        self.USERINFO_URL = settings.OIDC_USERINFO_URL
        self.SCOPES = settings.OIDC_SCOPES
        self.PERMISSION_ADMIN_NAME = "admin"
        self.PERMISSION_MANAGE_NAME = "manage"
        ADMIN_PATTERN=settings.OIDC_PERMISSION_ADMIN_PATTEREN
        MANAGE_PATTERN=settings.OIDC_PERMISSION_MANAGE_PATTEREN
        self.PERMISSION_MAP = {"admin": ADMIN_PATTERN, "manage": MANAGE_PATTERN}
        self.OIDC_GROUPS_PATH = settings.OIDC_GROUPS_PATH
        self.DEFAULT_ROLE = settings.OIDC_DEFAULT_ROLE
        self.DEBUG=settings.OIDC_DEBUG
        self.DEBUG=False
        self.ENABLE=settings.OIDC_ENABLED
        self.LOGOUT_URL=settings.OIDC_LOGOUT_URL
        
class NewLogoutView(LogoutView):
    
    def dispatch(self, request, *args, **kwargs):
        if settings.OIDC_LOGOUT_URL!="" and settings.OIDC_ENABLED:
            if settings.OIDC_DEBUG:
                print("logout")
                print("redirect to -> ",settings.OIDC_LOGOUT_URL)
            return redirect(settings.OIDC_LOGOUT_URL)
        return super().dispatch(request, *args, **kwargs)
    