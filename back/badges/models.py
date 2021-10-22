from django.db import models

from misc.models import Content, File
from organization.models import BaseTemplate


class Badge(BaseTemplate):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)
    content = models.ManyToManyField(Content)
