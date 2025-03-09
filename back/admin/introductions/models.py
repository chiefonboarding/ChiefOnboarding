from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from organization.models import BaseItem, Notification


class Introduction(BaseItem):
    intro_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Person to introduce"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

    @property
    def update_url(self):
        return reverse("introductions:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("introductions:delete", args=[self.id])

    def get_icon_template(self):
        return render_to_string("_intro_icon.html")

    @property
    def notification_add_type(self):
        return Notification.Type.ADDED_INTRODUCTION
