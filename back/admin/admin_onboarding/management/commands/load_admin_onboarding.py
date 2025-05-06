import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Loads the admin onboarding fixtures"

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, "fixtures/admin_onboarding.json")
        
        self.stdout.write(self.style.SUCCESS("Loading admin onboarding fixtures..."))
        call_command("loaddata", fixture_path, verbosity=1)
        self.stdout.write(self.style.SUCCESS("Admin onboarding fixtures loaded successfully!"))
