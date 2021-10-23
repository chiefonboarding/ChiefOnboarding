import uuid

import pyotp
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from admin.integrations.models import AccessToken
# from google_auth_oauthlib.flow import Flow
from organization.models import Organization
from users.serializers import NewHireSerializer

from .serializers import LoginSerializer


def logged_in_user_redirect(request):
    print("got hererrr")
    if request.user.is_admin_or_manager:
        return redirect("people")


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                request,
                username=serializer.data["username"],
                password=serializer.data["password"],
            )
            if user is not None:
                # check TOTP
                if user.requires_otp:
                    totp_input = serializer.data["totp"].strip().replace(" ", "")

                    if totp_input == "":
                        return Response(
                            {"totp": "provide_totp"}, status=status.HTTP_400_BAD_REQUEST
                        )

                    totp = pyotp.TOTP(user.totp_secret)
                    otp_recovery_key = user.check_otp_recovery_key(totp_input)
                    if (
                        not totp.verify(totp_input) and otp_recovery_key is None
                    ) or cache.get(user.email) != None:
                        return Response(
                            {"error": "TOTP code does not match"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    cache.set(user.email, "passed", 30)

                login(request, user)
                translation.activate(request.user.language)
                user = NewHireSerializer(request.user)
                return Response(user.data)
        return Response(
            {"error": _("Username and password do not match. Please try again.")},
            status=status.HTTP_400_BAD_REQUEST,
        )


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        #         access_code = AccessToken.objects.filter(integration=3)
        #         org = Organization.objects.get()
        #         if access_code.exists():
        #             access_code = access_code.first()
        #             # TODO: proper error handling necessary.
        #             try:
        #                 flow = Flow.from_client_config(client_config={
        #                     "web":
        #                         {"client_id": access_code.client_id,
        #                          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        #                          "token_uri": "https://oauth2.googleapis.com/token",
        #                          "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        #                          "client_secret": access_code.client_secret,
        #                          "redirect_uris": [settings.BASE_URL + "/api/auth/google_login"],
        #                          "javascript_origins": [settings.BASE_URL]}},
        #                     scopes=['https://www.googleapis.com/auth/userinfo.email', 'openid'], redirect_uri=settings.BASE_URL + "/api/auth/google_login")
        #                 flow.fetch_token(code=request.GET.get('code', ''))
        #                 session = flow.authorized_session()
        #                 results = session.get('https://openidconnect.googleapis.com/v1/userinfo').json()
        #             except:
        #                 return redirect('/#/?error=not_found')
        #             if 'email' in results:
        #                 users = get_user_model().objects.filter(email=results['email'].lower())
        #                 if users.exists() and org.google_login:
        #                     user = users.first()
        #                     user.backend = 'django.contrib.auth.backends.ModelBackend'
        #                     login(request, user)
        #                     if user.role == 1 or user.role == 2:
        #                         return redirect('/#/admin/')
        #                     else:
        #                         return redirect('/#/portal/')
        #
        return redirect("/#/?error=not_found")
