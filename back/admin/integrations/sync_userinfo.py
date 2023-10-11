from django.contrib.auth import get_user_model

from admin.integrations.exceptions import KeyIsNotInDataError
from admin.integrations.utils import get_value_from_notation
from admin.integrations.mixins import PaginatedResponse
from admin.people.serializers import UserImportSerializer
from organization.models import Organization

import logging

logger = logging.getLogger(__name__)


class SyncUsers(PaginatedResponse):
    """
    Syncing can be done in two ways:
    1. Creating new users.
    2. Updating the users with a specific value.
    These two options can be available through the same manifest and can be scheduled.
    Paginated response is supported.
    """
    def __init__(self, integration):
        super().__init__(integration)
        self.users = self.get_data_from_paginated_response()

    def run(self):
        action = self.integration.manifest.get("action", "create")
        if action == "create":
            new_users = self.get_import_user_candidates()
            self.create_users(new_users)

        elif action == "update":
            self.update_users()

    def update_users(self):
        # Email param is currently hardcoded, no way to change
        emails = [user["email"] for user in self.users]
        users_dict = {u["email"]: u for u in self.users}

        user_objects = get_user_model().objects.filter(email__in=emails)
        for user in user_objects:
            user_info = users_dict.get(user.email)
            # remove user email attr as we already have that on the instance
            user_info.pop("email")
            user.extra_fields.update(user_info)

        get_user_model().objects.bulk_update(user_objects, ["extra_fields"])

    def create_users(self, new_users):
        serializer = UserImportSerializer(data=new_users, many=True)
        valid_ones = []

        if serializer.is_valid():
            serializer.save(is_active=False)
        else:
            # if we have errors, then only get the valid ones
            for idx, error in enumerate(serializer.errors):
                if not len(error):
                    valid_ones.append(new_users[idx])
                else:
                    logger.info(f"Couldn't save {new_users[idx]['email']} due to {error}")

        # push them again through the function to save the users
        if len(valid_ones):
            self.create_users(valid_ones)

    def get_import_user_candidates(self):
        # Remove users that are already in the system or have been ignored
        existing_user_emails = list(
            get_user_model().objects.all().values_list("email", flat=True)
        )
        ignored_user_emails = Organization.objects.get().ignored_user_emails
        excluded_emails = (
            existing_user_emails + ignored_user_emails + ["", None]
        )  # also add blank emails to ignore

        user_candidates = [
            user_data
            for user_data in self.users
            if user_data.get("email", "") not in excluded_emails
        ]

        return user_candidates
