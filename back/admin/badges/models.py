from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse

from misc.models import File
from organization.models import BaseItem


class Badge(BaseItem):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
    content_json = models.JSONField(default=dict)

    def update_url(self):
        return reverse("badges:update", args=[self.id])

    def delete_url(self):
        return reverse("badges:delete", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_badge_icon.html")
