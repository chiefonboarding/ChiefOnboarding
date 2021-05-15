from django.db import models

from organization.models import BaseTemplate
from misc.models import Content


class Appointment(BaseTemplate):
    content = models.ManyToManyField(Content)
    time = models.TimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    fixed_date = models.BooleanField(default=False)
    on_day = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def duplicate(self):
        self.pk = None
        self.save()
