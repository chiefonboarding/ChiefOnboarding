from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse

from misc.fields import ContentJSONField
from organization.models import BaseItem


class Appointment(BaseItem):
    content = ContentJSONField(default=dict)
    time = models.TimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    fixed_date = models.BooleanField(default=False)
    on_day = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def get_icon_template(self):
        return render_to_string("_appointment_icon.html")

    def update_url(self):
        return reverse("appointments:update", args=[self.id])

    def delete_url(self):
        return reverse("appointments:delete", args=[self.id])
