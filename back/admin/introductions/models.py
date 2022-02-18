from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse

from organization.models import BaseItem


class Introduction(BaseItem):
    intro_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("introductions:update", args=[self.id])

    def delete_url(self):
        return reverse("introductions:delete", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_intro_icon.html")

    @property
    def notification_add_type(self):
        return "added_introduction"
