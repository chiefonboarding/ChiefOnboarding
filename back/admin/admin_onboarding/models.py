from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class AdminOnboardingStatus(models.Model):
    """
    Tracks the status of admin onboarding for each admin user.
    """
    class Status(models.IntegerChoices):
        NOT_STARTED = 0, _("Not Started")
        IN_PROGRESS = 1, _("In Progress")
        COMPLETED = 2, _("Completed")

    admin = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="onboarding_status",
        verbose_name=_("Admin")
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.NOT_STARTED,
        verbose_name=_("Status")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Admin Onboarding Status")
        verbose_name_plural = _("Admin Onboarding Statuses")

    def __str__(self):
        return f"{self.admin.full_name} - {self.get_status_display()}"
