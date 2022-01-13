from django.db import models
from django.urls import reverse

from django.template.loader import render_to_string
from misc.models import Content, File
from organization.models import BaseItem


class Badge(BaseItem):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)
    content = models.ManyToManyField(Content)

    def update_url(self):
        return reverse("badges:update", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_badge_icon.html")
