from django.core.mail import send_mail
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import translation
from organization.models import Organization


def send_sequence_message(new_hire, message):
    org = Organization.object.get()
    subject = _("Here is an update!")
    for i in message:
        t = Template(i.text)
        i.text = t.render(Context(
            {'manager': new_hire.manager.full_name(), 'buddy': new_hire.buddy.full_name(), 'position': new_hire.position,
             'last_name': new_hire.last_name, 'first_name': new_hire.first_name, 'email': new_hire.email}))
    html_message = render_to_string("email/base.html",
                                    {'org': org, 'content': message})
    message = ""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_hire.email], html_message=html_message)


def send_sequence_update_message(new_hire, message):
    org = Organization.object.get()
    subject = _("Here is an update!")
    blocks = []
    if len(message['to_do']) > 0:
        text = _('Todo item')
        if len(message['to_do']) > 1:
            text = _('Todo items')
        blocks.append({
            "type": 'p',
            "text": text
        })
        text = ""
        for i in message['to_do']:
            text += '- ' + new_hire.personalize(i.name) + '<br />'
        blocks.append({
            "type": 'block',
            "text": text
        })
    if len(message['resources']) > 0:
        text = _('Resource')
        if len(message['resources']) > 1:
            text = _('Resources')
        blocks.append({
            "type": 'p',
            "text": text
        })
        text = ""
        for i in message['resources']:
            text += '- ' + new_hire.personalize(i.name) + '<br />'
        blocks.append({
            "type": 'block',
            "text": text
        })
    if len(message['badges']) > 0:
        text = _('Badge')
        if len(message['badges']) > 1:
            text = _('Badges')
        blocks.append({
            "type": 'p',
            "text": text
        })
        text = ""
        for i in message['badges']:
            text += '- ' + new_hire.personalize(i.name) + '<br />'
        blocks.append({
            "type": 'block',
            "text": text
        })
    html_message = render_to_string("email/base.html",
                                    {'org': org, 'content': blocks})
    message = ""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_hire.email], html_message=html_message)
