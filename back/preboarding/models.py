from django.db import models

from organization.models import BaseTemplate, FullTemplateManager, FullManager
from misc.models import Content


class Preboarding(BaseTemplate):
    content = models.ManyToManyField(Content)
    form = models.JSONField(null=True, blank=True)
    picture = models.FileField(null=True)

    objects = FullManager()
    templates = FullTemplateManager()

    def __str__(self):
        return self.name
