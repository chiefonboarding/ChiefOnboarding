from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from misc.fields import ContentJSONField
from organization.models import BaseItem


class Preboarding(BaseItem):
    content = ContentJSONField(verbose_name=_("Content"), default=dict)
    form = models.JSONField(null=True, blank=True)
    picture = models.FileField(null=True)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("preboarding:update", args=[self.id])

    def delete_url(self):
        return reverse("preboarding:delete", args=[self.id])

    @property
    def get_icon_template(self):
        return render_to_string("_preboarding_icon.html")

    @property
    def notification_add_type(self):
        return "added_preboarding"
