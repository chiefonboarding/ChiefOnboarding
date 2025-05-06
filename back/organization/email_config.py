from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from anymail.backends.mailgun import EmailBackend as MailgunBackend
from anymail.backends.mailjet import EmailBackend as MailjetBackend
from anymail.backends.mandrill import EmailBackend as MandrillBackend
from anymail.backends.postmark import EmailBackend as PostmarkBackend
from anymail.backends.sendgrid import EmailBackend as SendgridBackend
from anymail.backends.sendinblue import EmailBackend as SendinblueBackend

# Custom backend for MailerSend
class MailerSendBackend:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        self.kwargs = kwargs

    def __call__(self, **kwargs):
        from anymail.message import AnymailMessage
        from anymail.backends.base import BasePayload

        # Configure Anymail with MailerSend settings
        settings.ANYMAIL = {
            "MAILERSEND_API_KEY": self.api_key,
        }

        # Return a custom backend that uses the MailerSend API
        return MailerSendEmailBackend()

class MailerSendEmailBackend:
    def __init__(self):
        from django.core.mail.backends.base import BaseEmailBackend
        self.backend = BaseEmailBackend()

    def send_messages(self, email_messages):
        """Send messages using the MailerSend API."""
        if not email_messages:
            return 0

        count = 0
        for message in email_messages:
            try:
                self._send(message)
                count += 1
            except Exception as e:
                if not getattr(message, 'fail_silently', False):
                    raise
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

        data = {
            "from": {
                "email": message.from_email,
            },
            "to": recipients,
            "subject": message.subject,
        }

        # Add HTML or plain text content
        if message.content_subtype == "html":
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
            return SMTPBackend(
                host=org.email_host,
                port=org.email_port,
                username=org.email_host_user,
                password=org.email_host_password,
                use_tls=org.email_use_tls,
                use_ssl=org.email_use_ssl,
                fail_silently=False,
            )
        elif org.email_provider == 'mailgun':
            return MailgunBackend(
                api_key=org.mailgun_api_key,
                sender_domain=org.mailgun_domain,
            )
        elif org.email_provider == 'mailjet':
            return MailjetBackend(
                api_key=org.mailjet_api_key,
                secret_key=org.mailjet_secret_key,
            )
        elif org.email_provider == 'mandrill':
            return MandrillBackend(
                api_key=org.mandrill_api_key,
            )
        elif org.email_provider == 'postmark':
            return PostmarkBackend(
                server_token=org.postmark_server_token,
            )
        elif org.email_provider == 'sendgrid':
            return SendgridBackend(
                api_key=org.sendgrid_api_key,
            )
        elif org.email_provider == 'sendinblue':
            return SendinblueBackend(
                api_key=org.sendinblue_api_key,
            )
        elif org.email_provider == 'mailersend':
            return MailerSendBackend(
                api_key=org.mailersend_api_key,
            )()
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
