from django.conf import settings
from django.db import models
from django.urls import reverse

from organization.models import BaseItem
from django.template.loader import render_to_string


class Introduction(BaseItem):
    intro_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("introductions:update", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_intro_icon.html")
