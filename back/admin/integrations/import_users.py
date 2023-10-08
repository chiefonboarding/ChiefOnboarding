from django.contrib.auth import get_user_model

from admin.integrations.mixins import PaginatedResponseMixin
from organization.models import Organization


class ImportUser(PaginatedResponseMixin):
    """
    Extracts all users and then checks which ones are not yet in the system,
    so we can show them as options when importing these.
    """

    def __init__(self, integration):
        self.integration = integration

    def get_import_user_candidates(self):
        users = self.get_data_from_paginated_response()

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
            for user_data in users
            if user_data.get("email", "") not in excluded_emails
        ]

        return user_candidates
