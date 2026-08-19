import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .s3 import S3


class File(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, blank=True)
    ext = models.CharField(max_length=10, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_files",
    )

    def get_url(self):
        return S3().get_file(self.key)

    def __str__(self):
        return self.key


@receiver(pre_delete, sender=File)
def remove_file(sender, instance, **kwargs):
    S3().delete_file(instance.key)


# This needs to stay here, not connected to anything.
# If we remove this model, then migrations will not be able to run.
# This model used to be connected to multiple models.
class Content(models.Model):
    pass
