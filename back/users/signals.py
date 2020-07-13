from users.models import User, NewHireDetails
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=NewHireDetails)
def generate_unique_url(sender, instance, created, **kwargs):
    if created:
        instance.generate_unique_url()
