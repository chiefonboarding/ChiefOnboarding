import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _

from organization.models import Organization, WelcomeMessage
from users.models import User


def email_new_admin_cred(user, password):
    translation.activate(user.language)
    org = Organization.object.get()
    subject = _("Your login credentials!")
    content = [
        {
            "type": "p",
            "text": _(
                "Someone in your organisation invited you to join ChiefOnboarding. Here are your login details:"
            ),
        },
        {
            "type": "block",
            "text": "<strong>Username:</strong>&nbsp;{user.email}<br /><strong>Password:</strong>&nbsp;{password}<strong><br />Login URL:</strong>&nbsp;{settings.BASE_URL}",
        },
    ]
    message = ""
    html_message = render_to_string(
        "email/base.html",
        {"first_name": user.first_name, "content": content, "org": org},
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def email_reopen_task(task, message, user):
    translation.activate(user.language)
    subject = _("Please redo this task")
    message_email = ""
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": "Hi {user.first_name}, we have just reopened this task. {message}",
        },
        {
            "type": "block",
            "text": "<strong>{task.to_do.name}</strong> <br />Go to your dashboard to complete it",
        },
        {"type": "button", "text": "Dashboard", "url": settings.BASE_URL},
    ]
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    send_mail(
        subject,
        message_email,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def send_reminder_email(task):
    subject = _("Please complete this task")
    message = ""
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": f"Hi {task.user.first_name}, Here is a quick reminder of the following task:",
        },
        {
            "type": "block",
            "text": f"<strong>{task.to_do.name}</strong> <br />Go to your dashboard to complete it.",
        },
        {"type": "button", "text": "Dashboard", "url": settings.BASE_URL},
    ]
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [task.user.email],
        html_message=html_message,
    )


def send_new_hire_credentials(new_hire):
    password = User.objects.make_random_password()
    org = Organization.object.get()
    new_hire.set_password(password)
    new_hire.send_login_email = True
    new_hire.save()
    subject = f"Welcome to {org.name}!"
    message = WelcomeMessage.objects.get(
        language=new_hire.language, message_type=1
    ).message
    personalized_message = new_hire.personalize(message)
    content = [
        {"type": "p", "text": personalized_message},
        {
            "type": "block",
            "text": "<strong>Username: {new_hire.email}</strong> <br /><strong>Password: </strong>{password}",
        },
        {"type": "button", "text": "Dashboard", "url": settings.BASE_URL},
    ]
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
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
    personalized_message = new_hire.personalize(message)
    subject = f"Welcome to {org.name}!"
    content = [
        {"type": "p", "text": personalized_message},
        {
            "type": "button",
            "text": "See pages",
            "url": f"{settings.BASE_URL}/#/preboarding/auth?token={new_hire.unique_url}",
        },
    ]
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    message = ""
    send_mail(
        subject,
        personalized_message,
        settings.DEFAULT_FROM_EMAIL,
        [new_hire.email],
        html_message=html_message,
    )
