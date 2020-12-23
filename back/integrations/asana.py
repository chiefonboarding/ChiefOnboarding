import os
from django.contrib.auth import get_user_model

from .models import AccessToken
import json
import requests


class UnauthorizedError(Exception):
    """Raised when the input value is too small"""
    pass


class Asana:
    account_id = None
    headers = {}
    BASE_URL = 'https://app.asana.com/api/1.0/'

    def __init__(self, team_id=None):
        asana_objects = AccessToken.objects.filter(active=True, integration=4)
        if asana_objects.exists():
            self.asana_obj = asana_objects.first()
            self.token = self.asana_obj.token
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.token
            }
            print(self.asana_obj.account_id)
            if self.asana_obj.account_id == None:
                account_id = self.get_org_id()
                self.asana_obj.account_id = account_id
                self.asana_obj.save()
            self.team_id = team_id
        else:
            raise UnauthorizedError

    def add_user_to_workspace(self, email):
        data = {
          "data": {
            "user": email
          }
        }
        r = requests.post(
            self.BASE_URL + "workspaces/" + str(self.asana_obj.account_id) + "/addUser", headers=self.headers, data=json.dumps(data))
        if r.status_code == 200:
            return True
        if r.status_code == 401:
            # token is not valid anymore
            self.asana_obj.active = False
            self.asana_obj.save()
            raise UnauthorizedError
        return False

    def add_user_to_team(self, email):
        data = {
          "data": {
            "user": email
          }
        }
        r = requests.post(
            self.BASE_URL + "teams/" + str(self.team_id) + "/addUser", headers=self.headers, data=json.dumps(data))
        if r.status_code == 200:
            return True
        if r.status_code == 401:
            # token is not valid anymore
            self.asana_obj.active = False
            self.asana_obj.save()
            raise UnauthorizedError
        return False

    def find_by_email(self, email):
        r = requests.get(self.BASE_URL + "users/" + email + "/teams?organization=" + self.asana_obj.account_id, headers=self.headers)
        if r.status_code == 200:
            return any(x for x in r.json()['data'] if x['gid'] == str(self.team_id))
        if r.status_code == 401:
            # token is not valid anymore
            self.asana_obj.active = False
            self.asana_obj.save()
            raise UnauthorizedError
        return False

    def get_org_id(self):
        r = requests.get(self.BASE_URL + "workspaces", headers=self.headers)
        if r.status_code == 200:
            return r.json()['data'][0]['gid']
        if r.status_code == 401:
            # token is not valid anymore
            self.asana_obj.active = False
            self.asana_obj.save()
            raise UnauthorizedError
        return False

    def get_teams(self):
        r = requests.get(self.BASE_URL + "organizations/" + self.asana_obj.account_id + "/teams", headers=self.headers)
        if r.status_code == 200:
            data = []
            for i in r.json()['data']:
                data.append({'name': i['name'], 'id': i['gid']})
            return data
        if r.status_code == 401:
            # token is not valid anymore
            self.asana_obj.active = False
            self.asana_obj.save()
            raise UnauthorizedError
        return False
