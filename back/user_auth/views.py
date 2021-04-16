from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import redirect
from django.utils import translation
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import NewHireSerializer
from django.utils.translation import gettext_lazy as _
from integrations.models import AccessToken
from google_auth_oauthlib.flow import Flow
from organization.models import Organization
from .serializers import LoginSerializer
import pyotp
import uuid

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(request, username=serializer.data['username'], password=serializer.data['password'])
            if user is not None:
                # check TOTP
                if user.requires_otp:
                    if serializer.data['totp'] == '':
                        return Response({'totp': 'provide_totp'},
                                        status=status.HTTP_400_BAD_REQUEST)

                    totp = pyotp.TOTP(user.totp_secret)
                    if not totp.verify(serializer.data['totp']) and not user.otp_recovery_key == serializer.data['totp']:
                        return Response({'error': 'TOTP code does not match'},
                                        status=status.HTTP_400_BAD_REQUEST)
                    if user.otp_recovery_key == serializer.data['totp']:
                        user.totp_secret = pyotp.random_base32()
                        user.otp_recovery_key = uuid.uuid4()
                        user.requires_otp = False
                        user.save()
                login(request, user)
                translation.activate(request.user.language)
                user = NewHireSerializer(request.user)
                return Response(user.data)
        return Response({'error': _('Username and password do not match. Please try again.')},
                        status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        access_code = AccessToken.objects.filter(integration=3)
        org = Organization.objects.get()
        if access_code.exists():
            access_code = access_code.first()
            # TODO: proper error handling necessary.
            try:
                flow = Flow.from_client_config(client_config={
                    "web":
                        {"client_id": access_code.client_id,
                         "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                         "token_uri": "https://oauth2.googleapis.com/token",
                         "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                         "client_secret": access_code.client_secret,
                         "redirect_uris": [settings.BASE_URL + "/api/auth/google_login"],
                         "javascript_origins": [settings.BASE_URL]}},
                    scopes=['https://www.googleapis.com/auth/userinfo.email', 'openid'], redirect_uri=settings.BASE_URL + "/api/auth/google_login")
                flow.fetch_token(code=request.GET.get('code', ''))
                session = flow.authorized_session()
                results = session.get('https://openidconnect.googleapis.com/v1/userinfo').json()
            except:
                return redirect('/#/?error=not_found')
            if 'email' in results:
                users = get_user_model().objects.filter(email=results['email'].lower())
                if users.exists() and org.google_login:
                    user = users.first()
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    if user.role == 1 or user.role == 2:
                        return redirect('/#/admin/')
                    else:
                        return redirect('/#/portal/')

        return redirect('/#/?error=not_found')
