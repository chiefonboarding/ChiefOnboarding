from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from misc.fields import ContentJSONField
from organization.models import BaseItem, Notification


class Appointment(BaseItem):
    content = ContentJSONField(verbose_name=_("Content"), default=dict)
    time = models.TimeField(verbose_name=_("Time"), blank=True, null=True)
    date = models.DateField(verbose_name=_("Date"), blank=True, null=True)
    fixed_date = models.BooleanField(verbose_name=_("Fixed date"), default=False)
    on_day = models.IntegerField(verbose_name=_("On day"), default=0)

    def __str__(self):
        return self.name

    def get_icon_template(self):
        return render_to_string("_appointment_icon.html")

    @property
    def notification_add_type(self):
        return Notification.Type.ADDED_APPOINTMENT

    @property
    def update_url(self):
        return reverse("appointments:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("appointments:delete", args=[self.id])
