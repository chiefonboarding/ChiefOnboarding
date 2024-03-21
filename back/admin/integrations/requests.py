import json
from datetime import timedelta
from django.utils import timezone
from django_q.tasks import schedule
from django_q.models import Schedule
import time
from admin.integrations.utils import get_value_from_notation
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from requests.exceptions import (
    HTTPError,
    InvalidHeader,
    InvalidJSONError,
    InvalidSchema,
    InvalidURL,
    JSONDecodeError,
    MissingSchema,
    SSLError,
    Timeout,
    TooManyRedirects,
    URLRequired,
)
import requests
import base64
from .alter_data import Placeholders
from .models import IntegrationTracker, IntegrationTrackerStep, ManifestExecute, ManifestInitialData
from organization.models import BaseItem, Notification

class BaseRequests:
    def __init__(self, integration, user, track=True, default_headers=None):
        self.default_headers = default_headers or {}
        self.integration = integration
        self.user = user

        self.placeholders = Placeholders(user=user, integration=integration)
        # Add generated secrets
        for item in ManifestInitialData.objects.filter(manifest=integration.manifest, name="generate"):
            self.placeholders.add({item.id: get_random_string(length=10)})

        self.available_files = {}
        self.tracker = None
        self.responses = []

        if track:
            self.tracker = IntegrationTracker(
                integration=self,
                for_user=user,
            )

    def _headers(self, request_headers):
        headers = request_headers or self.default_headers

        new_headers = {}
        for key, value in headers:
            # If Basic authentication then swap to base64
            if key == "Authorization" and value.startswith("Basic"):
                auth_details = self.placeholders.replace(value.split(" ", 1)[1])
                value = "Basic " + base64.b64encode(
                    auth_details.encode("ascii")
                ).decode("ascii")

            # Adding an empty string to force to return a string instead of a
            # safestring. Ref: https://github.com/psf/requests/issues/6159
            new_headers[self.placeholders.replace(key) + ""] = self.placeholders.replace(value) + ""
        return new_headers

    def _cast_to_json(self, value):
        try:
            value = json.loads(value)
        except Exception:
            pass

        return value

    def renew_key(self):
        # Oauth2 refreshing access token if needed
        success = True
        if (
            self.integration.has_oauth
            and "expires_in" in self.extra_args.get("oauth", {})
            and self.expiring < timezone.now()
        ):
            success, response = self.run_request(self.manifest["oauth"]["refresh"])

            if not success:
                user = self.new_hire if self.has_user_context else None
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_INTEGRATION,
                    extra_text=self.name,
                    created_for=user,
                    description="Refresh url: " + str(response),
                )
                return success

            self.extra_args["oauth"] |= response.json()
            if "expires_in" in response.json():
                self.expiring = timezone.now() + timedelta(
                    seconds=response.json()["expires_in"]
                )
            self.save(update_fields=["expiring", "extra_args"])
            if hasattr(self, "tracker"):
                # we need to clean the last step as we now probably got new secret keys
                # that need to be masked
                last_step = self.tracker.steps.last()
                last_step.json_response = self.clean_response(last_step.json_response)
                last_step.save()

        return success



    def make_request(self, url, method, data, headers, save_as_file="", files={}, status_code=[], cast_data_to_json=False):
        url = self.placeholders.replace(url)
        post_data = self.placeholders.replace(json.dumps(data["data"]))
        headers = self._headers(headers)

        if cast_data_to_json:
            post_data = self._cast_to_json(post_data)

        error = ""

        # extract files from locally saved files and send them with the request
        files_to_send = {}
        for field_name, file_name in files:
            try:
                files_to_send[field_name] = (file_name, self.available_files[file_name])
            except KeyError:
                error = f"{file_name} could not be found in the locally saved files"
                if self.tracker:
                    IntegrationTrackerStep.objects.create(
                        status_code=0,
                        tracker=self.tracker,
                        json_response={},
                        text_response=error,
                        url=self.placeholders.sanitize(url),
                        method=method,
                        post_data=json.loads(
                            self.placeholders.sanitize(json.dumps(post_data))
                        ),
                        headers=json.loads(
                            self.placeholders.sanitize(json.dumps(headers))
                        ),
                        error=error,
                    )
                return False, error

        # now actually make the request
        response = None
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=post_data,
                files=files_to_send,
                timeout=120,
            )
        except (InvalidJSONError, JSONDecodeError):
            error = "JSON is invalid"

        except HTTPError:
            error = "An HTTP error occurred"

        except SSLError:
            error = "An SSL error occurred"

        except Timeout:
            error = "The request timed out"

        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL):
            error = "The url is invalid"

        except TooManyRedirects:
            error = "There are too many redirects"

        except InvalidHeader:
            error = "The header is invalid"

        except:  # noqa E722
            error = "There was an unexpected error with the request"

        if response and error == "" and status_code and response.status_code not in status_code:
            error = f"Incorrect status code ({response.status_code}): {self.placeholders.sanitize(response.text)}"

        # try to make sense out of text/json response
        try:
            json_response = response.json()
            text_response = ""
        except:  # noqa E722
            json_response = {}
            if error:
                text_response = error
            else:
                text_response = response.text

        if self.tracker:
            response_payload = self.placeholders.sanitize(json.dumps(json_response))
            if cast_data_to_json:
                post_data = json.dumps(post_data)
            post_payload = self.placeholders.sanitize(post_data)
            headers_payload = self.placeholders.sanitize(post_data)

            IntegrationTrackerStep.objects.create(
                status_code=0 if response is None else response.status_code,
                tracker=self.tracker,
                json_response=json.loads(response_payload),
                text_response=(
                    _("Cannot display, could be file")
                    if save_as_file
                    else self.placeholders.sanitize(text_response)
                ),
                url=self.placeholders.sanitize(url),
                method=method,
                post_data=post_payload,
                headers=headers_payload,
                error=self.placeholders.sanitize(error),
            )


        # save if file, so we can reuse later
        if save_as_file:
            self.available_files[save_as_file] = io.BytesIO(response.content)

        # save json response temporarily to be reused in other parts
        try:
            self.responses.append(response.json())
        except:  # noqa E722
            # if we save a file, then just append an empty dict
            self.responses.append({})

        if error:
            return False, error

        return True, response
