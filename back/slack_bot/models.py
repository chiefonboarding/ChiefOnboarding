from django.db import models

from .utils import Slack


class SlackChannelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def update_channels(self):
        channels = Slack().get_channels()
        for channel_name, is_private in channels:
            self.get_or_create(name=channel_name, defaults={"is_private": is_private})


class SlackChannel(models.Model):
    name = models.CharField(max_length=1000)
    is_private = models.BooleanField(default=False)

    objects = SlackChannelManager()

    def __str__(self):
        return self.name
