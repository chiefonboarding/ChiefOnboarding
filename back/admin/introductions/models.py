from django.conf import settings
from django.db import models
from django.urls import reverse

from organization.models import BaseItem


class Introduction(BaseItem):
    intro_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("introductions:update", args=[self.id])
