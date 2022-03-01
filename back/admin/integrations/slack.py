import json
import os

import requests
import slack_sdk as slack
from django.contrib.auth import get_user_model

from .emails import slack_error_email
from .models import AccessToken


class Error(Exception):
    """Base class for other exceptions"""

    pass


class PaidOnlyError(Error):
    """Raised when the input value is too small"""

    pass


class UnauthorizedError(Error):
    """Raised when the input value is too small"""

    pass


class Slack:
    auth_session = None
    credentials = None
    record = None
    integration_type = 1
    BASE_URL = "https://slack.com/api/"

    def __init__(self):
        self.access_obj = AccessToken.objects.filter(
            active=True, integration=self.integration_type
        )
        if self.access_obj.count() == 0:
            raise Error("No tokens available")

        self.access_obj = AccessToken.objects.filter(
            active=True, integration=self.integration_type
        ).first()

    def get_token(self):
        return self.access_obj.token

    def exists(self):
        return self.record is not None

    def get_authentication_header(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.get_token()),
        }

    def add_user(self, email, channels):
        r = requests.post(
            f"{self.BASE_URL}/users.admin.invite?token={self.get_token()}&email={email}channel_ids={channels}",
            headers=self.get_authentication_header(),
        )
        if r.json()["ok"]:
            return True
        return False

    def delete_user(self, email):
        response = requests.post(
            f"{self.BASE_URL}/users.admin.setInactive?token={self.get_token()}&email={email}",
            headers=self.get_authentication_header(),
        )
        if response.json()["ok"]:
            return True
        raise False

    def get_channels(self):
        response = requests.post(
            f"{self.BASE_URL}/conversations.list?token={self.get_token()}&exclude_archived=true&types=public_channel,private_channel",
            headers=self.get_authentication_header(),
        )
        return [[x["name"], x["is_private"]] for x in response["channels"]]
