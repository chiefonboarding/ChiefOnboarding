from django.conf import settings
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import gettext as _

from organization.models import Organization


def send_access_email(user, password, email):
    translation.activate(user.language)
    subject = _("Here are your email login credentials!")
    message = _(
        "Hi %(name)s!\n\nI have just created a new email account for you. Here are the "
        "details: \n\nYour brand new email address: %(email)s\nPassword: %(password)s"
        "\n\nAnd you can login here: https://gmail.com \n\nTalk soon!"
    ) % {"name": user.first_name, "email": user.email, "password": password}
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


def google_error_email(user):
    translation.activate(user.language)
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": _(
                "We tried to create a Google account for one of your new hires, but "
                "unfortunately, Google denied that request. Access we had to your "
                "organization in Google has likely been revoked. Please go to your "
                "website and reconnect your Google account to complete this."
            ),
        }
    ]
    html_message = org.create_email({"org": org, "content": content})
    send_mail(
        _("Oh no, we couldn't create a Google account for you new hire!"),
        "",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def slack_error_email(user):
    translation.activate(user.language)
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": _(
                "We tried to create a Slack account for one of your new hires, but "
                "unfortunately, Slack denied that request. Your key has likely been "
                "revoked. Please go to our website and reconnect your Slack account "
                "to complete this."
            ),
        }
    ]
    html_message = org.create_email({"org": org, "content": content})
    send_mail(
        _("Oh no, we couldn't create a Slack account for you new hire!"),
        "",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
