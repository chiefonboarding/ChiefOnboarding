from django.contrib.auth import get_user_model

from admin.integrations.utils import get_value_from_notation
from admin.integrations.mixins import PaginatedResponseMixin

import logging

logger = logging.getLogger(__name__)


class SyncUsers(PaginatedResponseMixin):
    """
    Sync some data from a third party to our users. This can be anything that is
    presented in a list form from the users. Matching happens based on the email
    property from the response data. Paginated response is supported.
    """

    def __init__(self, integration):
        self.integration = integration

    def sync_user_info(self):
        users = self.get_data_from_paginated_response()

        # get user emails so we can fetch all users from the db (without having to
        # make a bunch of queries). Email param is currently hardcoded, no way to change
        emails = [user["email"] for user in users]

        user_objects = get_user_model().objects.filter(email__in=emails)

        for user in user_objects:
            user_info = next((u for u in users if u["email"] == user.email))

            store_data = self.integration.manifest.get("sync_data", {})

            for new_hire_prop, notation_for_response in store_data.items():
                try:
                    value = get_value_from_notation(notation_for_response, user_info)
                except KeyError:
                    logger.info(
                        f"Could not store data to new hire ({user.email}): "
                        f"{notation_for_response} not found in "
                        f"{self.integration.clean_response(user_info)} for {user.email}"
                    )
                    continue

                user.extra_fields[new_hire_prop] = value

        get_user_model().objects.bulk_update(user_objects, ["extra_fields"])
