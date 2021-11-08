# import google.oauth2.credentials
# from google.auth.transport.requests import AuthorizedSession
import json

from .models import AccessToken

# from google.auth.transport import Request


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
    auth_session = None
    credentials = None
    record = None

    def __init__(self):
        google_code = AccessToken.objects.filter(active=True, integration=2)
        # if google_code.exists():
        #     self.record = google_code.first()
        #     self.credentials = google.oauth2.credentials.Credentials(token=self.record.token,
        #                                                              refresh_token=self.record.refresh_token,
        #                                                              token_uri='https://www.googleapis.com/oauth2/v4/token',
        #                                                              client_id=self.record.client_id,
        #                                                              client_secret=self.record.client_secret)
        #     self.auth_session = AuthorizedSession(self.credentials)
        # if datetime.now() > self.record.expiring:
        # 	self.refresh()

    def exists(self):
        return self.record is not None

    def refresh(self):
        self.credentials.refresh(Request)
        self.record.token_encrypt = self.credentials.token
        self.record.expiring = self.credentials.expiry
        self.record.save()

    def find_by_email(self, email):
        response = self.auth_session.get(
            "https://www.googleapis.com/admin/directory/v1/users?customer=my_customer&query=email%3D" + email.lower()
        )
        if "users" in response.json():
            return True
        return False

    def get_all_users(self):
        response = self.auth_session.get("https://www.googleapis.com/admin/directory/v1/users?customer=my_customer")
        if "users" in response.json():
            return response.json()["users"]
        return False

    def add_user(self, payload):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "charset": "UTF-8",
        }
        response = self.auth_session.post(
            "https://www.googleapis.com/admin/directory/v1/users",
            data=json.dumps(payload),
            headers=headers,
        )

        if response.status_code == 400:
            if response.json()["error"]["errors"][0]["reason"] == "invalid":
                raise EmailAddressNotValidError
        if response.status_code == 403 or response.status_code == 404:
            raise EmailAddressNotValidError
        if response.status_code == 401:
            raise UnauthorizedError
        if response.status_code == 200:
            return
