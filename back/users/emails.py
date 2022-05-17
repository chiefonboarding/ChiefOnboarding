from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from organization.models import Organization, WelcomeMessage
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
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def email_reopen_task(task_name, message, user):
    translation.activate(user.language)
    subject = _("Please redo this task")
    message_email = ""
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
    send_mail(
        subject,
        message_email,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def send_reminder_email(task_name, user):
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
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def send_new_hire_credentials(new_hire_id):
    new_hire = User.objects.get(id=new_hire_id)
    password = User.objects.make_random_password()
    org = Organization.object.get()
    new_hire.set_password(password)
    new_hire.save()
    subject = f"Welcome to {org.name}!"
    message = WelcomeMessage.objects.get(
        language=new_hire.language, message_type=1
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
        {"type": "button", "data": {"text": _("Dashboard"), "url": settings.BASE_URL}},
    ]
    html_message = org.create_email({"org": org, "content": content, "user": new_hire})
    message = ""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [new_hire.email],
        html_message=html_message,
    )


def send_new_hire_preboarding(new_hire):
    org = Organization.object.get()
    message = WelcomeMessage.objects.get(
        language=new_hire.language, message_type=0
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
    send_mail(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [new_hire.email],
        html_message=html_message,
    )
