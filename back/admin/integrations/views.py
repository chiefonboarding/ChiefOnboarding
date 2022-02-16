import json

import requests
from django.conf import settings
from django.shortcuts import redirect

# from google_auth_oauthlib.flow import Flow
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccessToken


class SlackOAuthView(APIView):
    def get(self, request):
        access_token = AccessToken.objects.get(integration=0)
        if "code" not in request.GET:
            return redirect("/#/admin/newhire?slack=notok")
        code = request.GET["code"]
        params = {
            "code": code,
            "client_id": access_token.client_id,
            "client_secret": access_token.client_secret,
            "redirect_uri": access_token.redirect_url,
        }
        url = "https://slack.com/api/oauth.v2.access"
        json_response = requests.get(url, params)
        data = json.loads(json_response.text)
        if data["ok"]:
            access_token.bot_token = data["access_token"]
            access_token.bot_id = data["bot_user_id"]
            access_token.token = data["access_token"]
            access_token.save()
        return redirect("/#/admin/newhire")


class SlackCreateAccountView(APIView):
    def get(self, request):
        access_token = AccessToken.objects.get(integration=1)
        if "code" not in request.GET:
            return redirect("/#/admin/newhire?slack=notok")
        code = request.GET["code"]
        params = {
            "code": code,
            "client_id": access_token.client_id,
            "client_secret": access_token.client_secret,
            "redirect_uri": access_token.redirect_url,
        }
        url = "https://slack.com/api/oauth.v2.access"
        json_response = requests.get(url, params)
        data = json.loads(json_response.text)
        if data["ok"]:
            access_token.token = data["access_token"]
            access_token.save()
        return redirect("/#/admin/newhire")
