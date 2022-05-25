import smtplib
from django.core.mail import send_mail
from django.conf import settings
from anymail.exceptions import (
    AnymailRecipientsRefused,
    AnymailAPIError,
    AnymailInvalidAddress,
)

from organization.models import Notification


def send_email_with_notification(
    subject, to, notification_type, html_message="", message="", created_for=None
):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            html_message=html_message,
            fail_silently=False,
        )
    except AnymailRecipientsRefused as e:
        Notification.objects.create(
            notification_type="failed_email_recipients_refused",
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except AnymailAPIError as e:
        Notification.objects.create(
            notification_type="failed_email_delivery",
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except AnymailInvalidAddress as e:
        Notification.objects.create(
            notification_type="failed_email_address",
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except smtplib.SMTPException as e:
        Notification.objects.create(
            notification_type="failed_email_delivery",
            created_for=created_for,
            extra_text=subject,
            description=str(e),
        )
    else:
        Notification.objects.create(
            notification_type=notification_type,
            created_for=created_for,
            extra_text=subject,
        )
