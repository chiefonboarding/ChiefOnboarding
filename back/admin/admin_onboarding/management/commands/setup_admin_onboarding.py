import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sets up the admin onboarding process by running migrations and loading fixtures"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up admin onboarding..."))
        
        # Run migrations
        self.stdout.write(self.style.SUCCESS("Running migrations..."))
        call_command("migrate", "admin_onboarding", verbosity=1)
        
        # Load fixtures
        self.stdout.write(self.style.SUCCESS("Loading admin onboarding fixtures..."))
        fixture_path = os.path.join(settings.BASE_DIR, "fixtures/admin_onboarding.json")
        call_command("loaddata", fixture_path, verbosity=1)
        
        self.stdout.write(self.style.SUCCESS("Admin onboarding setup completed successfully!"))
