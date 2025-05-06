import json
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
    # Get organization to check for custom from_email
    from organization.models import Organization
    org = Organization.object.get()

    # Use custom from_email if set, otherwise use default
    from_email = settings.DEFAULT_FROM_EMAIL
    if org.email_from_name and org.email_from_name.strip():
        # Format as "Custom Name <email@domain.com>"
        if '<' in from_email and '>' in from_email:
            # Already has format "Name <email>"
            email_part = from_email.split('<')[1]
            from_email = f"{org.email_from_name} <{email_part}"
        else:
            # Just an email address
            from_email = f"{org.email_from_name} <{from_email}>"

    try:
        send_mail(
            subject,
            message,
            from_email,
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


def has_manager_or_buddy_tags(content_json):
    if content_json is None:
        return False, False

    # convert to string and then remove all spaces, so we can easily match
    content_str = json.dumps(content_json)
    content_str_no_spaces = "".join(content_str.split())

    manager_tags = ["{{manager}}", "{{manager_email}}"]
    buddy_tags = ["{{buddy}}", "{{buddy_email}}"]

    requires_manager = any([tag in content_str_no_spaces for tag in manager_tags])
    requires_buddy = any([tag in content_str_no_spaces for tag in buddy_tags])

    return requires_manager, requires_buddy
