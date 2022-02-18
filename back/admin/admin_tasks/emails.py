from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _

from organization.models import Organization


def send_email_notification_to_external_person(admin_task):
    subject = _("Can you please do this for me?")
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": _("Hi! Could you please help me with this? It's for our new hire %(name)s") % {'name': admin_task.new_hire.full_name()}
        }
    ]
    if admin_task.comment.exists():
        content.append({"type": "block", "text": admin_task.content.last().comment})
    message = ""
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_task.email],
        html_message=html_message,
    )


def send_email_new_assigned_admin(admin_task):
    translation.activate(admin_task.new_hire.language)
    subject = _("A task has been assigned to you!")
    org = Organization.object.get()
    content = [
        {
            "type": "p",
            "text": _("This is about task: %(title)s for %(new_hire)s") % {'title': admin_task.name, 'new_hire': admin_task.new_hire.full_name()},
        }
    ]
    if admin_task.comment.exists():
        content.append(
            {
                "type": "block",
                "text": "<strong>"
                + _("Last message: ")
                + "</strong><br />"
                + admin_task.content.last().comment,
            }
        )
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    send_mail(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [admin_task.assigned_to.email],
        html_message=html_message,
    )


def send_email_new_comment(comment):
    translation.activate(comment.admin_task.assigned_to.language)
    subject = _("Someone added something to task: %(task_name)s") % {'task_name': comment.admin_task.name}
    org = Organization.object.get()
    content = [
        {"type": "p", "text": _("Hi %(name)s") % {'name': comment.admin_task.assigned_to.first_name}},
        {
            "type": "p",
            "text": _(
                "One of your todo items has been updated by someone else. Here is the message:"
            ),
        },
        {
            "type": "block",
            "text": comment.content + "<br />" + "- " + comment.comment_by.full_name,
        },
    ]
    html_message = render_to_string("email/base.html", {"org": org, "content": content})
    send_mail(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [comment.admin_task.assigned_to.email],
        html_message=html_message,
    )
