from django.conf import settings
from django.db import models

from organization.models import BaseItem


class Introduction(BaseItem):
    intro_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
