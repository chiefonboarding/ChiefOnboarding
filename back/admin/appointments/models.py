from django.db import models
from django.urls import reverse

from misc.models import Content
from organization.models import BaseItem


class Appointment(BaseItem):
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

    def update_url(self):
        return reverse("appointments:update", args=[self.id])

    def delete_url(self):
        return reverse("appointments:delete", args=[self.id])
