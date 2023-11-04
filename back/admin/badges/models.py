from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from misc.fields import ContentJSONField
from misc.models import File
from organization.models import BaseItem, Notification


class Badge(BaseItem):
    image = models.ForeignKey(
        File, verbose_name=_("Image"), on_delete=models.SET_NULL, null=True, blank=True
    )
    content = ContentJSONField(verbose_name=_("Content"), default=dict)

    @property
    def update_url(self):
        return reverse("badges:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("badges:delete", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_badge_icon.html")

    @property
    def notification_add_type(self):
        return Notification.Type.ADDED_BADGE
