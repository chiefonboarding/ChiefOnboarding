from django.conf import settings
from django.db import migrations


def migrate_email_settings(apps, schema_editor):
    """
    Migrate email settings from environment variables to the database.
    """
    Organization = apps.get_model('organization', 'Organization')
    
    try:
        org = Organization.objects.get(id=1)
        
        # Set default from email
        if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
            org.default_from_email = settings.DEFAULT_FROM_EMAIL
        
        # Determine which email provider is configured
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            # SMTP is configured
            org.email_provider = 'smtp'
            org.email_host = settings.EMAIL_HOST
            org.email_port = settings.EMAIL_PORT
            org.email_host_user = settings.EMAIL_HOST_USER
            org.email_host_password = settings.EMAIL_HOST_PASSWORD
            org.email_use_tls = settings.EMAIL_USE_TLS
            org.email_use_ssl = settings.EMAIL_USE_SSL
        elif hasattr(settings, 'ANYMAIL') and settings.ANYMAIL:
            # Anymail provider is configured
            if 'MAILGUN_API_KEY' in settings.ANYMAIL:
                org.email_provider = 'mailgun'
                org.mailgun_api_key = settings.ANYMAIL.get('MAILGUN_API_KEY', '')
                org.mailgun_domain = settings.ANYMAIL.get('MAILGUN_SENDER_DOMAIN', '')
            elif 'MAILJET_API_KEY' in settings.ANYMAIL:
                org.email_provider = 'mailjet'
                org.mailjet_api_key = settings.ANYMAIL.get('MAILJET_API_KEY', '')
                org.mailjet_secret_key = settings.ANYMAIL.get('MAILJET_SECRET_KEY', '')
            elif 'MANDRILL_API_KEY' in settings.ANYMAIL:
                org.email_provider = 'mandrill'
                org.mandrill_api_key = settings.ANYMAIL.get('MANDRILL_API_KEY', '')
            elif 'POSTMARK_SERVER_TOKEN' in settings.ANYMAIL:
                org.email_provider = 'postmark'
                org.postmark_server_token = settings.ANYMAIL.get('POSTMARK_SERVER_TOKEN', '')
            elif 'SENDGRID_API_KEY' in settings.ANYMAIL:
                org.email_provider = 'sendgrid'
                org.sendgrid_api_key = settings.ANYMAIL.get('SENDGRID_API_KEY', '')
            elif 'SENDINBLUE_API_KEY' in settings.ANYMAIL:
                org.email_provider = 'sendinblue'
                org.sendinblue_api_key = settings.ANYMAIL.get('SENDINBLUE_API_KEY', '')
        
        org.save()
    except Organization.DoesNotExist:
        # Organization doesn't exist yet, nothing to migrate
        pass
    except Exception:
        # If there's any error, just skip the migration
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_add_email_provider_settings'),
    ]

    operations = [
        migrations.RunPython(migrate_email_settings, migrations.RunPython.noop),
    ]
