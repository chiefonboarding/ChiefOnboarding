from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admin.admin_tasks.models import AdminTask
from misc.fields import ContentJSONField
from organization.models import BaseItem, Notification


class Hardware(BaseItem):
    class PersonType(models.IntegerChoices):
        MANAGER = 1, _("Manager")
        BUDDY = 2, _("Buddy")
        CUSTOM = 3, _("Custom")

    content = ContentJSONField(default=dict, verbose_name=_("Content"))
    person_type = models.IntegerField(
        verbose_name=_("Assigned to"),
        choices=PersonType.choices,
        null=True,
        blank=True,
        help_text=_(
            "Leave empty to automatically remove/add hardware without notifications."
        ),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Pick user"),
        on_delete=models.CASCADE,
        related_name="assigned_user_hardware",
        null=True,
        blank=True,
    )

    def remove_or_add_to_user(self, user):
        add = not user.is_offboarding
        if add:
            user.hardware.add(self)
        else:
            user.hardware.remove(self)

        Notification.objects.create(
            notification_type=self.notification_add_type
            if add
            else self.notification_remove_type,
            extra_text=self.name,
            created_for=user,
            item_id=self.id,
        )

    def execute(self, user):
        add = not user.is_offboarding

        if self.person_type is None:
            # no person assigned, so add directly
            self.remove_or_add_to_user(user)
            return

        if self.person_type == Hardware.PersonType.MANAGER:
            assigned_to = user.manager
        elif self.person_type == Hardware.PersonType.BUDDY:
            assigned_to = user.buddy
        else:
            assigned_to = self.assigned_to

        if add:
            admin_task_name = _(
                "Send hardware to new hire (%(new_hire)s): %(name)s"
            ) % {"new_hire": user.full_name, "name": self.name}
        else:
            admin_task_name = _(
                "Reclaim hardware from employee (%(new_hire)s): %(name)s"
            ) % {"new_hire": user.full_name, "name": self.name}

        AdminTask.objects.create_admin_task(
            new_hire=user,
            assigned_to=assigned_to,
            name=admin_task_name,
            hardware=self,
        )

    def get_icon_template(self):
        return render_to_string("_hardware_icon.html")

    @property
    def notification_add_type(self):
        return Notification.Type.ADDED_HARDWARE

    @property
    def notification_remove_type(self):
        return Notification.Type.REMOVED_HARDWARE

    @property
    def update_url(self):
        return reverse("hardware:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("hardware:delete", args=[self.id])
