from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

# Custom backend for MailerSend
class MailerSendBackend:
    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        self.api_key = api_key
        self.fail_silently = fail_silently
        self.kwargs = kwargs

    def __call__(self, **kwargs):
        # Configure Anymail with MailerSend settings
        settings.ANYMAIL = {
            "MAILERSEND_API_KEY": self.api_key,
        }

        # Return a custom backend that uses the MailerSend API
        return MailerSendEmailBackend(fail_silently=self.fail_silently)

class MailerSendEmailBackend(BaseEmailBackend):
    """
    A Django email backend for MailerSend.
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._connection = None
        self._lock = None

    def open(self):
        """
        Ensure we have an API key for MailerSend.
        """
        if self._connection:
            return True

        try:
            # Check if we have an API key
            api_key = settings.ANYMAIL.get("MAILERSEND_API_KEY")
            if not api_key:
                raise ValueError("MailerSend API key is required")

            self._connection = True
            return True
        except Exception as e:
            if not self.fail_silently:
                raise e
            return False

    def close(self):
        """
        Close the connection to the API.
        """
        self._connection = None

    def send_messages(self, email_messages):
        """Send messages using the MailerSend API."""
        if not email_messages:
            return 0

        # Make sure we have a connection
        if not self._connection:
            if not self.open():
                return 0

        count = 0
        for message in email_messages:
            try:
                self._send(message)
                count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise e
        return count

    def _send(self, message):
        """Send a single message using the MailerSend API."""
        import requests
        import json

        # Get the API key from settings
        api_key = settings.ANYMAIL.get("MAILERSEND_API_KEY")
        if not api_key:
            raise ValueError("MailerSend API key is required")

        # Prepare the email data
        recipients = []
        for to_email in message.to:
            recipients.append({"email": to_email})

        # Process the from_email field
        from_email = message.from_email
        from_name = None

        # Check if from_email contains a name part
        if '<' in from_email and '>' in from_email:
            # Format is "Name <email@example.com>"
            from_name = from_email.split('<')[0].strip()
            from_email = from_email.split('<')[1].split('>')[0].strip()

        # Prepare the from data
        from_data = {"email": from_email}
        if from_name:
            from_data["name"] = from_name

        data = {
            "from": from_data,
            "to": recipients,
            "subject": message.subject,
        }

        # Add HTML or plain text content
        if hasattr(message, 'content_subtype') and message.content_subtype == "html":
            data["html"] = message.body
        else:
            data["text"] = message.body

        # Send the request to the MailerSend API
        response = requests.post(
            "https://api.mailersend.com/v1/email",
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Authorization": f"Bearer {api_key}",
            },
            data=json.dumps(data),
        )

        # Check for errors
        if response.status_code != 202:
            raise Exception(f"MailerSend API error: {response.text}")


def get_email_backend():
    """
    Get the email backend based on the organization settings.
    If no provider is configured in the database, fall back to the environment settings.
    """
    from organization.models import Organization

    try:
        org = Organization.object.get()

        # If no provider is selected, fall back to environment settings
        if not org.email_provider:
            return None

        # Configure the email backend based on the selected provider
        if org.email_provider == 'smtp':
            # For SMTP, we need to return the backend instance with configuration
            return "django.core.mail.backends.smtp.EmailBackend"
        elif org.email_provider == 'mailgun':
            # For Anymail backends, we return the path to the backend class
            settings.ANYMAIL = {
                "MAILGUN_API_KEY": org.mailgun_api_key,
                "MAILGUN_SENDER_DOMAIN": org.mailgun_domain,
            }
            return "anymail.backends.mailgun.EmailBackend"
        elif org.email_provider == 'mailjet':
            settings.ANYMAIL = {
                "MAILJET_API_KEY": org.mailjet_api_key,
                "MAILJET_SECRET_KEY": org.mailjet_secret_key,
            }
            return "anymail.backends.mailjet.EmailBackend"
        elif org.email_provider == 'mandrill':
            settings.ANYMAIL = {
                "MANDRILL_API_KEY": org.mandrill_api_key,
            }
            return "anymail.backends.mandrill.EmailBackend"
        elif org.email_provider == 'postmark':
            settings.ANYMAIL = {
                "POSTMARK_SERVER_TOKEN": org.postmark_server_token,
            }
            return "anymail.backends.postmark.EmailBackend"
        elif org.email_provider == 'sendgrid':
            settings.ANYMAIL = {
                "SENDGRID_API_KEY": org.sendgrid_api_key,
            }
            return "anymail.backends.sendgrid.EmailBackend"
        elif org.email_provider == 'sendinblue':
            settings.ANYMAIL = {
                "SENDINBLUE_API_KEY": org.sendinblue_api_key,
            }
            return "anymail.backends.sendinblue.EmailBackend"
        elif org.email_provider == 'mailersend':
            # For MailerSend, we need to configure the API key
            settings.ANYMAIL = {
                "MAILERSEND_API_KEY": org.mailersend_api_key,
            }
            # Return the path to our custom backend
            return "organization.email_config.MailerSendEmailBackend"
    except Exception:
        # If there's any error, fall back to environment settings
        return None

    # If no provider is matched, fall back to environment settings
    return None


def get_default_from_email():
    """
    Get the default from email based on the organization settings.
    If no default from email is configured in the database, fall back to the environment settings.
    """
    from organization.models import Organization

    try:
        org = Organization.object.get()

        # If a default from email is configured, use it
        if org.default_from_email:
            return org.default_from_email
    except Exception:
        pass

    # Fall back to environment settings
    return settings.DEFAULT_FROM_EMAIL
