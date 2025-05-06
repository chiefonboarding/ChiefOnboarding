from django.apps import AppConfig
from django.conf import settings


class OrganizationConfig(AppConfig):
    name = "organization"

    def ready(self):
        """
        Configure email settings from the database when the app is ready.
        This is called when the application starts.
        """
        # Avoid circular imports
        from organization.email_config import get_email_backend, get_default_from_email

        # Only run in the main process, not in management commands or other subprocesses
        if not settings.DEBUG and not settings.RUNNING_TESTS:
            try:
                # Try to get the email backend from the database
                email_backend = get_email_backend()
                if email_backend:
                    # Replace the default email backend with our custom one
                    settings.EMAIL_BACKEND = email_backend

                # Try to get the default from email from the database
                default_from_email = get_default_from_email()
                if default_from_email:
                    # Replace the default from email with our custom one
                    settings.DEFAULT_FROM_EMAIL = default_from_email
            except Exception:
                # If there's any error, just use the environment settings
                pass
