#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    from organization.models import Organization
    if 'migrate' in sys.argv and Organization.objects.all().count() == 0:
        from django.conf import settings
        from users.models import User
        from django.utils.crypto import get_random_string
        from django.core import management

        if settings.ACCOUNT_EMAIL != '' and settings.ACCOUNT_PASSWORD != '':
            username = settings.ACCOUNT_EMAIL
            password = settings.ACCOUNT_PASSWORD
        else:
            username = get_random_string(length=6).lower() + '@example.com'
            password = get_random_string(length=4)

            print("""
                ----------------------------------------
                ----------------------------------------
                PASSWORD AND USERNAME FOR FIRST LOG IN.
                PLEASE CREATE A NEW ACCOUNT AND DELETE THIS ONE
                Username: %s Password: %s
                ----------------------------------------
                ----------------------------------------""" % (username, password))
        User.objects.create_admin("Demo", "User", username, password)
        Organization.objects.create(name="Demo organization")
        welcome_message_path = os.path.join(settings.BASE_DIR, 'fixtures/welcome_message.json')
        all_path = os.path.join(settings.BASE_DIR, 'fixtures/all.json')
        management.call_command('loaddata', welcome_message_path, verbosity=0)
        management.call_command('loaddata', all_path, verbosity=0)

if __name__ == '__main__':
    main()
