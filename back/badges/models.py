from django.contrib.postgres.fields import JSONField
from django.db import models

from organization.models import BaseTemplate
from misc.models import Content, File


class Badge(BaseTemplate):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)
    content = models.ManyToManyField(Content)

