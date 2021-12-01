from django.db import models
from django.urls import reverse

from misc.models import Content
from organization.models import BaseItem


class Preboarding(BaseItem):
    content = models.ManyToManyField(Content)
    form = models.JSONField(null=True, blank=True)
    picture = models.FileField(null=True)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("preboarding:update", args=[self.id])
