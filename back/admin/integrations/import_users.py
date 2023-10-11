from django.contrib.auth import get_user_model

from admin.integrations.mixins import PaginatedResponseMixin
from organization.models import Organization


class ImportUser(PaginatedResponse):
    """
    Extracts all users and then checks which ones are not yet in the system,
    so we can show them as options when importing these.
    """

    def __init__(self, integration):
        self.integration = integration

