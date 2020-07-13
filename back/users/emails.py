from django.core.mail import send_mail
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import translation
from organization.models import Organization
import uuid

# from back.organization.models import WelcomeMessage


def email_new_admin_cred(user, password):
    translation.activate(user.language)
    org = Organization.object.get()
    subject = _("Your login credentials!")
    content = [
        {
            "type": "p",
            "text": _('Someone in your organisation invited you to join ChiefOnboarding. Here are your login details:')
        }, {
            "type": "block",
            "text": "<strong>" + _('Username:') + "</strong>&nbsp;" + user.email + "<br /><strong>" + _('Password:') +
                    "</strong>&nbsp;" + password + "<strong><br />" + _('Login URL:') + "</strong>&nbsp;" + settings.BASE_URL
        }
    ]
    message = ""
    html_message = render_to_string("email/base.html", {'first_name': user.first_name, 'content': content, 'org': org})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)


def email_reopen_task(task, message, user):
    translation.activate(user.language)
    subject = _("Please redo this task")
    message_email = ""
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": 'Hi ' + user.first_name + ', ' + _('we have just reopened this task.') + message
        }, {
            "type": "block",
            "text": "<strong>" + task.to_do.name + "</strong> <br />" + _('Go to your dashboard to complete it.')
        }, {
            "type": "button",
            "text": "Dashboard",
            "URL": settings.BASE_URL
        }
    ]
    html_message = render_to_string("email/base.html", {'org': org, 'content': content})
    send_mail(subject, message_email, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)


def send_reminder_email(task):
    subject = _("Please complete this task")
    message = ""
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": 'Hi ' + task.user.first_name + ', ' + _('Here is a quick reminder of the following task:')
        }, {
            "type": "block",
            "text": "<strong>" + task.to_do.name + "</strong> <br />" + _('Go to your dashboard to complete it.')
        }, {
            "type": "button",
            "text": "Dashboard",
            "URL": settings.BASE_URL
        }
    ]
    html_message = render_to_string("email/base.html", {'org': org, 'content': content})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [task.user.email], html_message=html_message)


def send_new_hire_cred(new_hire, message):
    password = uuid.uuid4().hex[:12].upper()
    org = Organization.object.get()
    new_hire.set_password(password)
    new_hire.send_login_email = True
    new_hire.save()
    subject = _("Welcome to " + org.name + "!")
    message = new_hire.personalize(message)
    content = [
        {
            "type": "p",
            "text": message
        }, {
            "type": "block",
            "text": "<strong>Username: " + new_hire.email + "</strong> <br /><strong>Password: </strong>" + password
        }, {
            "type": "button",
            "text": "Dashboard",
            "URL": settings.BASE_URL
        }
    ]
    html_message = render_to_string("email/base.html",
                                    {'org': org, 'content': content})
    message = ""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_hire.email], html_message=html_message)


def send_new_hire_preboarding(new_hire, message):
    org = Organization.object.get()
    subject = _("Welcome to " + org.name + "!")
    message = new_hire.personalize(message)
    html_message = render_to_string("email/base.html",
                                    {'org': org, 'content': [{'type': 'p', 'text': message}]})
    message = ""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_hire.email], html_message=html_message)

