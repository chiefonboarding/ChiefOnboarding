from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings

from organization.models import Organization



class IntegrationEmail:
    user = None
    org = None

    def __init__(self, user):
        self.user = user
        translation.activate(user.language)
        self.org = Organization.object.get()


    def send_access_email(self, password, email):
        subject = _("Here are your email login credentials!")
        message = _("Hi ") + user.first_name + _(
            "! \n\nI have just created a new email account for you. Here are the details: \n\nYour brand new email "
            "address: ") + user.email + \
                  _("\nPassword: ") + password + _(" \nAnd you can login here: https://gmail.com \n\nTalk soon!")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


    def google_auth_error_email(self):    
        content = [
            {
                "type": "p",
                "text": _('We tried to create a Google account for one of your new hires, but unfortunately, Google denied'
                          'that request. Access we had to your organization in Google has likely been revoked. Please go'
                          'to your website and reconnect your Google account to complete this.')

            }
        ]
        self.send_email(
            subject=_("Oh no, we couldn't create a Google account for you new hire!"),
            content=content
        )


    def google_email_error_email(user, new_hire_email):
        content = [
            {
                "type": "p",
                "text": _('There was an error with adding the email address (' + new_hire_email + ') of your new hire. '
                          'Please make sure that it has been entered correctly. Feel free to try again by going to the '
                          'new hire\'s page and enable the Google integration.')

            }
        ]
        self.send_email(
            subject=_("Oh no, we couldn't create a Google account for you new hire!"),
            content=content
        )

    def slack_error_email(user):
        content = [
            {
                "type": "p",
                "text": _('We tried to create a Slack account for one of your new hires, but unfortunately, Slack denied '
                          'that request. Your key has likely been revoked. Please go to our website and reconnect your '
                          'Slack account to complete this.')

            }
        ]
        self.send_email(
            subject=_("Oh no, we couldn't create a Slack account for you new hire!"),
            content=content
        )


    def asana_error_email(user):
        content = [
            {
                "type": "p",
                "text": _('We tried to add a new hire to your asana team, but we were not able to do that. Your key has likely '
                          'been revoked. Please go to our website and add your asana key again.')
            }
        ]
        self.send_email(
            subject=_("Oh no, we couldn't add your new hire to your Asana team!"),
            content=content
        )

    def send_email(self, subject, content):
        html_message = render_to_string("email/base.html", {'org': self.org, 'content': content})
        send_mail(_("Oh no, we couldn't create a Google account for you new hire!"), '', settings.DEFAULT_FROM_EMAIL, [self.user.email], html_message=html_message)

