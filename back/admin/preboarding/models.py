from django.db import models

from misc.models import Content
from organization.models import BaseItem, FullManager, FullTemplateManager


class Preboarding(BaseItem):
    content = models.ManyToManyField(Content)
    form = models.JSONField(null=True, blank=True)
    picture = models.FileField(null=True)

    objects = FullManager()
    templates = FullTemplateManager()

    def __str__(self):
        return self.name
