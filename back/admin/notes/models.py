from django.conf import settings
from django.db import models


class Note(models.Model):
    new_hire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="new_hire")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin")
    created = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=5000)
