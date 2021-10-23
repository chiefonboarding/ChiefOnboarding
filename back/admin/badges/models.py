from django.db import models

from misc.models import Content, File
from organization.models import BaseItem


class Badge(BaseItem):
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)
    content = models.ManyToManyField(Content)
