import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .s3 import S3


class File(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, blank=True)
    ext = models.CharField(max_length=10, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

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
