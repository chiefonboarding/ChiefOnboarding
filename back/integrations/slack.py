import os
import slack
from django.contrib.auth import get_user_model

from .emails import IntegrationEmail
from .models import AccessToken
import json
import requests


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

    def __init__(self):
        slack_code = AccessToken.objects.filter(active=True, integration=1)
        if slack_code.exists():
            self.record = slack_code.first()
            self.auth_session = slack.WebClient(token=self.record.token)
        # if datetime.now() > self.record.expiring:
        # 	self.refresh()

    def exists(self):
        return self.record is not None

    def add_user(self, email):
        r = requests.get(
            "https://slack.com/api/users.admin.invite?token=" + self.record.token + "&email=" + email)
        if r.json()['ok']:
            return
        elif 'error' in r.json() and (r.json()['error'] == 'already_in_team' or r.json()['error'] == 'already_invited'):
            return
        elif 'error' in r.json() and r.json()['error'] == 'token_revoked':
            self.record.active = False
            self.record.save()
            raise UnauthorizedError
        return Error

    def delete_user(self, email):
        response = requests.get(
            "https://slack.com/api/users.admin.setInactive?token=" + self.record.token + "&user=" + email)
        if response.json()['ok']:
            return True
        else:
            if response.json()['error'] == 'paid_only':
                raise PaidOnlyError
            elif response.json()['error'] == 'not_found':
                return True
            else:
                raise Error
