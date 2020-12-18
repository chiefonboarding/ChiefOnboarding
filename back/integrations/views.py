from django.conf import settings
from django.shortcuts import redirect
from google_auth_oauthlib.flow import Flow
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import json

from .models import AccessToken, ScheduledAccess
from .serializers import SlackTokenSerializer, GoogleAPITokenSerializer, GoogleOAuthTokenSerializer, \
    ScheduledAccessSerializer, AsanaSerializer
from .asana import Asana

class SlackTokenCreateView(generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = AccessToken.objects.all()
    serializer_class = SlackTokenSerializer


class GoogleTokenCreateView(generics.CreateAPIView):
    queryset = AccessToken.objects.all()
    serializer_class = GoogleAPITokenSerializer


class AsanaCreateView(generics.CreateAPIView):
    queryset = AccessToken.objects.all()
    serializer_class = AsanaSerializer


class GoogleAddTokenView(APIView):
    def get(self, request):
        access_code = AccessToken.objects.filter(integration=2)
        if access_code.exists() and str(access_code.first().one_time_auth_code) == request.GET.get('state', ''):
            access_code = access_code.first()
            flow = Flow.from_client_config(client_config={
                "web":
                    {"client_id": access_code.client_id,
                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                     "token_uri": "https://oauth2.googleapis.com/token",
                     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                     "client_secret": access_code.client_secret,
                     "redirect_uris": [settings.BASE_URL + "/api/integrations/google_token"],
                     "javascript_origins": [settings.BASE_URL]}},
                scopes=['https://www.googleapis.com/auth/admin.directory.user', ],
                redirect_uri=settings.BASE_URL + "/api/integrations/google_token")
            flow.fetch_token(code=request.GET.get('code', ''))
            credentials = flow.credentials
            access_code.token = credentials.token
            access_code.refresh_token = credentials.refresh_token
            access_code.expiring = credentials.expiry
            access_code.save()
        return redirect('/#/admin/newhire')


class GoogleLoginTokenCreateView(generics.CreateAPIView):
    queryset = AccessToken.objects.all()
    serializer_class = GoogleOAuthTokenSerializer


class SlackOAuthView(APIView):
    def get(self, request):
        access_token = AccessToken.objects.get(integration=0)
        if 'code' not in request.GET:
            return redirect('/#/admin/newhire?slack=notok')
        code = request.GET['code']
        params = {
            'code': code,
            'client_id': access_token.client_id,
            'client_secret': access_token.client_secret
        }
        url = 'https://slack.com/api/oauth.access'
        json_response = requests.get(url, params)
        data = json.loads(json_response.text)
        if data['ok']:
            access_token.bot_token = data['bot']['bot_access_token']
            access_token.bot_id = data['bot']['bot_user_id']
            access_token.token = data['access_token']
            access_token.save()
        return redirect('/#/admin/newhire')


class SlackCreateAccountView(APIView):
    def get(self, request):
        access_token = AccessToken.objects.get(integration=1)
        if 'code' not in request.GET:
            return redirect('/#/admin/newhire?slack=notok')
        code = request.GET['code']
        params = {
            'code': code,
            'client_id': access_token.client_id,
            'client_secret': access_token.client_secret
        }
        url = 'https://slack.com/api/oauth.access'
        json_response = requests.get(url, params)
        data = json.loads(json_response.text)
        if data['ok']:
            access_token.token = data['access_token']
            access_token.save()
        return redirect('/#/admin/newhire')


class TokenRemoveView(APIView):

    def delete(self, request, id):
        AccessToken.objects.filter(integration=id).delete()
        return Response()


class AsanaTeamsView(APIView):
    def get(self, request):
        teams = Asana().get_teams()
        return Response(teams)


class AccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows books/resources to be viewed or edited.
    """
    queryset = ScheduledAccess.objects.all()
    serializer_class = ScheduledAccessSerializer
