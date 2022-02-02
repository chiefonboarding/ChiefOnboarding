import json
import requests
from datetime import datetime, timedelta

from .models import AccessToken


class Error(Exception):
    """Base class for other exceptions"""

    pass


class EmailAddressNotValidError(Error):
    """Raised when the input value is too small"""

    pass


class UnauthorizedError(Error):
    """Raised when the input value is too small"""

    pass


class Asana:
    access_obj = AccessToken.objects.none()
    integration_type = 4
    BASE_URL = 'https://app.asana.com/api/1.0/'

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
        return self.access_obj.access_token

    def get_authentication_header(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.get_token())
        }

    def find_by_email(self, email, team_id):
        r = requests.get(f"{self.BASE_URL}users/{email}/teams?organization={self.access_obj.account_id}", headers=self.get_authentication_header())
        if r.status_code == 200:
            return any(x for x in r.json()['data'] if x['gid'] == str(team_id))
        return False

    def get_org_id(self):
        r = requests.get(f"{self.BASE_URL}workspaces", headers=self.get_authentication_header())
        if r.status_code == 200:
            self.access_obj.account_id = r.json()['data'][0]['gid']
            self.access_obj.save()
            return self.access_obj.account_id
        return False


    def add_user(self, email, team_id):
        data = {
          "data": {
            "user": email
          }
        }
        r = requests.post(
            f"{self.BASE_URL}teams/{team_id}/addUser",
            data=json.dumps(data),
            headers=self.get_authentication_header(),
        )
        if r.status_code == 200:
            return True
        return False


    def get_teams(self):
        # Just in case the account id hasn't ben fetched yet
        if self.access_obj.account_id == "":
            self.access_obj.account_id = self.get_org_id()

        r = requests.get(f"{self.BASE_URL}organizations/{self.access_obj.account_id}/teams", headers=self.get_authentication_header())
        if r.status_code == 200:
            return [{'name': i['name'], 'id': i['gid']} for i in r.json()['data']]
        return False
