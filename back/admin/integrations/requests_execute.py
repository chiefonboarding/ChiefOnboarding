from .requests import BaseRequests
from .models import IntegrationTracker, IntegrationTrackerStep, ManifestExecute, ManifestInitialData
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


class RunExecuteRequests(BaseRequests):

    def run(self, integration, retry_on_failure=False):
        if self.tracker is not None:
            self.tracker.category = IntegrationTracker.Category.EXECUTE
            self.tracker.save()

        for execute in ManifestExecute.objects.filter(manifest__integration=integration):
            success, response = self.make_request(
                url=execute.url,
                method=execute.method,
                data=execute.data,
                headers=execute.headers,
                save_as_file=execute.save_as_file,
                files=execute.files,
                cast_data_to_json=execute.cast_data_to_json
            )

            # check if we need to poll before continuing
            if execute.polling:
                success, response = self._polling(execute, response)

            # check if we need to block this integration based on condition
            if execute.continue_if:
                got_expected_result = self._check_condition(response, execute.continue_if)
                if not got_expected_result:
                    response = self.placeholders.sanitize(text=response)
                    Notification.objects.create(
                        notification_type=Notification.Type.BLOCKED_INTEGRATION,
                        extra_text=integration.name,
                        created_for=self.user,
                        description=f"Execute url ({execute.url}): {response}",
                    )
                    return False, response

            if not success:
                response = self.placeholders.sanitize(text=json.dumps(response))
                if execute.polling:
                    response = "Polling timed out: " + response
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_INTEGRATION,
                    extra_text=self.name,
                    created_for=self.user,
                    description=f"Execute url ({execute.url}): {self.placeholders.sanitize(json.dumps(response))}",
                )
                if retry_on_failure:
                    # Retry url in one hour
                    schedule(
                        "admin.integrations.tasks.retry_integration",
                        self.user.id,
                        integration.id,
                        params,
                        name=(
                            f"Retrying integration {integration.id} for user {self.user.id}"
                        ),
                        next_run=timezone.now() + timedelta(hours=1),
                        schedule_type=Schedule.ONCE,
                    )
                return False, response

            # store data coming back from response to the user, so we can reuse in other
            # integrations
            for new_hire_prop, notation_for_response in execute.store_data.items():
                try:
                    value = get_value_from_notation(
                        notation_for_response, response.json()
                    )
                except KeyError:
                    return (
                        False,
                        f"Could not store data to new hire: {notation_for_response}"
                        f" not found in {self.placeholders.replace(json.dumps(response.json()))}",
                    )

                # save to new hire and to temp var `params` on this model for use in
                # the same integration
                self.user.extra_fields[new_hire_prop] = value
            self.user.save(fields=["extra_fields"])
            self.placeholders.add_user_extra_fields()


    def _polling(self, item, response):
        polling = item.polling
        continue_if = item.continue_if
        interval = polling.get("interval")
        amount = polling.get("amount")

        got_expected_result = self._check_condition(response, continue_if)
        if got_expected_result:
            return True, response

        tried = 1
        while amount > tried:
            time.sleep(interval)
            success, response = self.run_request(item)
            got_expected_result = self._check_condition(response, continue_if)
            if got_expected_result:
                return True, response
            tried += 1
        # if exceeding the max amounts, then fail
        return False, response


    def _check_condition(self, response, condition):
        value = self.placeholders.replace(condition["value"])
        try:
            # first argument will be taken from the response
            response_value = get_value_from_notation(
                condition["response_notation"], response.json()
            )
        except KeyError:
            # we know that the result might not be in the response yet, as we are
            # waiting for the correct response, so just respond with an empty string
            response_value = ""
        return value == response_value
