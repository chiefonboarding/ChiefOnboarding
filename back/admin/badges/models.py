from django.db import models
from django.urls import reverse

from misc.models import Content, File
from organization.models import BaseItem


class Badge(BaseItem):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)
    content = models.ManyToManyField(Content)

    def update_url(self):
        return reverse("badges:update", args=[self.id])
