from django.core.management.base import BaseCommand
from django.utils import timezone

from organization.models import Organization


class Command(BaseCommand):
    help = (
        "Resets the timed_triggers_last_check on the org model to avoid unnecessary "
        "trigger runs when developing"
    )

    def handle(self, *args, **options):
        try:
            org = Organization.objects.get()
        except Organization.DoesNotExist:
            # skip if org has not been created yet
            return

        org.timed_triggers_last_check = timezone.now()
        org.save()
