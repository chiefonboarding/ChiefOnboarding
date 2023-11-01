from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from organization.models import Notification, Organization, WelcomeMessage
from organization.utils import send_email_with_notification
from users.models import User


def email_new_admin_cred(user):
    password = User.objects.make_random_password()
    user.set_password(password)
    user.save()
    translation.activate(user.language)
    org = Organization.object.get()
    subject = _("Your login credentials!")
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": _(
                    "Someone in your organisation invited you to join ChiefOnboarding."
                    "Here are your login details:"
                ),
            },
        },
        {
            "type": "quote",
            "data": {
                "text": "<strong>"
                + _("Username:")
                + f"</strong>&nbsp;{user.email}<br /><strong>"
                + _("Password:")
                + f"</strong>&nbsp;{password}<strong><br />"
                + _("Login URL:")
                + f"</strong>&nbsp;{settings.BASE_URL}",
            },
        },
    ]
    message = ""

    html_message = org.create_email(
        {"first_name": user.first_name, "content": content, "org": org, "user": user},
    )
    send_email_with_notification(
        subject=subject,
        message=message,
        to=user.email,
        created_for=user,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_LOGIN_CREDENTIALS,
    )


def email_reopen_task(task_name, message, user):
    translation.activate(user.language)
    subject = _("Please redo this task")
    org = Organization.object.get()
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": _("Hi %(name)s, we have just reopened this task. %(message)s")
                % {"name": user.first_name, "message": message},
            },
        },
        {
            "type": "quote",
            "data": {
                "text": _(
                    "<strong>%(task_name)s</strong> <br />Go to your dashboard to "
                    "complete it"
                )
                % {"task_name": task_name},
            },
        },
        {"type": "button", "data": {"text": _("Dashboard"), "url": settings.BASE_URL}},
    ]
    html_message = org.create_email({"org": org, "content": content, "user": user})
    send_email_with_notification(
        subject=subject,
        message=message,
        to=user.email,
        created_for=user,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_TASK_REOPENED,
    )


def send_reminder_email(task_name, user):
    translation.activate(user.language)
    subject = _("Please complete this task")
    message = ""
    org = Organization.object.get()
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": (
                    _("Hi %(name)s, Here is a quick reminder of the following task:")
                )
                % {"name": user.first_name},
            },
        },
        {
            "type": "quote",
            "data": {
                "text": _(
                    "<strong>%(task_name)s</strong> <br />Go to your dashboard to "
                    "complete it"
                )
                % {"task_name": task_name},
            },
        },
        {"type": "button", "data": {"text": _("Dashboard"), "url": settings.BASE_URL}},
    ]
    html_message = org.create_email({"org": org, "content": content, "user": user})
    send_email_with_notification(
        subject=subject,
        message=message,
        created_for=user,
        to=user.email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_TASK_REMINDER,
    )


def send_new_hire_credentials(new_hire_id, save_password=True, language=None):
    new_hire = User.objects.get(id=new_hire_id)
    org = Organization.object.get()

    if language is None:
        translation.activate(new_hire.language)
        language = new_hire.language

    password = "FAKEPASSWORD"
    if save_password:
        # For sending test emails, we don't actually want to save this password
        password = User.objects.make_random_password()
        new_hire.set_password(password)
        new_hire.save()
    subject = f"Welcome to {org.name}!"
    message = WelcomeMessage.objects.get(
        language=language, message_type=WelcomeMessage.Type.NEWHIRE_WELCOME
    ).message
    content = [
        {"type": "paragraph", "data": {"text": message}},
        {
            "type": "quote",
            "data": {
                "text": "<strong>"
                + _("Username: ")
                + f"</strong>{new_hire.email}<br /><strong>"
                + _("Password: ")
                + f"</strong>{password}",
            },
        },
        {"type": "button", "data": {"text": _("Dashboard"), "url": settings.WELCOME_URL}},
    ]
    html_message = org.create_email({"org": org, "content": content, "user": new_hire})
    message = ""
    send_email_with_notification(
        subject=subject,
        created_for=new_hire,
        message=message,
        to=new_hire.email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_NEWHIRE_CRED,
    )


def send_new_hire_preboarding(new_hire, email, language=None):
    org = Organization.object.get()

    if language is None:
        language = new_hire.language
        translation.activate(new_hire.language)

    message = WelcomeMessage.objects.get(
        language=language, message_type=WelcomeMessage.Type.PREBOARDING
    ).message
    subject = _("Welcome to %(name)s!") % {"name": org.name}
    content = [
        {"type": "paragraph", "data": {"text": message}},
        {
            "type": "button",
            "data": {
                "text": _("See pages"),
                "url": settings.BASE_URL
                + reverse("new_hire:preboarding-url")
                + "?token="
                + new_hire.unique_url,
            },
        },
    ]
    html_message = org.create_email({"org": org, "content": content, "user": new_hire})
    message = ""
    send_email_with_notification(
        subject=subject,
        created_for=new_hire,
        message=message,
        to=email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_PREBOARDING_ACCESS,
    )
