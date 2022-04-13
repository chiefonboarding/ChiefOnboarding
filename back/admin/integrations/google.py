import json
from datetime import datetime, timedelta

import requests

from .models import Integration


class Error(Exception):
    """Base class for other exceptions"""

    pass


class EmailAddressNotValidError(Error):
    """Raised when the input value is too small"""

    pass


class UnauthorizedError(Error):
    """Raised when the input value is too small"""

    pass


class Google:
    access_obj = Integration.objects.none()
    integration_type = 2

    def __init__(self):
        self.access_obj = Integration.objects.filter(
            active=True, integration=self.integration_type
        )
        if self.access_obj.count() == 0:
            raise Error("No tokens available")

        self.access_obj = Integration.objects.filter(
            active=True, integration=self.integration_type
        ).first()

    def get_token(self):
        # Add in a bit of margin so it has time to process requests
        if self.access_obj.expiring < (datetime.now() + timedelta(minutes=1)):
            return self.access_obj.token

        # Refresh token if token is not valid anymore
        r = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.access_obj.client_id,
                "client_secret": self.access_obj.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.access_obj.refresh_token,
            },
        )
        results = r.json()

        self.access_obj.token = results.access_token
        self.access_obj.expiring = datetime.now() + timedelta(
            seconds=results["expires_in"]
        )
        self.access_obj.ttl = results["expires_in"]
        self.access_obj.save()
        return results.access_token

    def get_authentication_header(self):
        return {"Authorization": "Bearer {}".format(self.get_token())}

    def find_by_email(self, email):
        r = requests.post(
            (
                "https://www.googleapis.com/admin/directory/v1/users?customer="
                f"my_customer&query=email%3D{email.lower}"
            ),
            headers=self.get_authentication_header(),
        )
        # if users is in the response, then the user was found
        return "users" in r.json()

    def get_all_users(self):
        r = requests.post(
            "https://www.googleapis.com/admin/directory/v1/users?customer=my_customer",
            headers=self.get_authentication_header(),
        )
        if "users" in r.json():
            return r.json()["users"]
        return []

    def add_user(self, payload):
        r = requests.post(
            "https://www.googleapis.com/admin/directory/v1/users",
            data=json.dumps(payload),
            headers=self.get_authentication_header(),
        )
        if r.status_code == 400:
            if r.json()["error"]["errors"][0]["reason"] == "invalid":
                raise EmailAddressNotValidError
        if r.status_code == 403 or r.status_code == 404:
            raise EmailAddressNotValidError
        if r.status_code == 401:
            raise UnauthorizedError
        if r.status_code == 200:
            return
