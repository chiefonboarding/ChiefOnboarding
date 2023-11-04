import smtplib

from anymail.exceptions import (
    AnymailAPIError,
    AnymailInvalidAddress,
    AnymailRecipientsRefused,
)
from django.conf import settings
from django.core.mail import send_mail

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
            notification_type=Notification.Type.FAILED_EMAIL_RECIPIENTS_REFUSED,
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except AnymailAPIError as e:
        Notification.objects.create(
            notification_type=Notification.Type.FAILED_EMAIL_DELIVERY,
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except AnymailInvalidAddress as e:
        Notification.objects.create(
            notification_type=Notification.Type.FAILED_EMAIL_ADDRESS,
            created_for=created_for,
            extra_text=subject,
            description=e.message,
        )
    except smtplib.SMTPException as e:
        Notification.objects.create(
            notification_type=Notification.Type.FAILED_EMAIL_DELIVERY,
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
