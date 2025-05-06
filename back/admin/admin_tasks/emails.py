from django.utils import translation
from django.utils.translation import gettext as _

from organization.models import Notification, Organization
from organization.utils import send_email_with_notification


def send_email_notification_to_external_person(admin_task):
    subject = _("Can you please do this for me?")
    org = Organization.object.get()
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": _(
                    "Hi! Could you please help me with this? It's for our new "
                    "hire %(name)s"
                )
                % {"name": admin_task.new_hire.full_name},
            },
        },
        {"type": "header", "data": {"level": 2, "text": admin_task.name}},
    ]
    if admin_task.comment.exists():
        content.append(
            {"type": "quote", "data": {"text": admin_task.comment.last().content}}
        )
    html_message = org.create_email(
        {"org": org, "content": content, "user": admin_task.new_hire}
    )
    send_email_with_notification(
        subject=subject,
        message="",
        to=admin_task.email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_ADMIN_TASK_EXTRA,
    )


def send_email_new_assigned_admin(admin_task):
    org = Organization.object.get()

    # Check if email notifications for admin tasks are enabled
    if not org.email_admin_task_notifications:
        return

    translation.activate(admin_task.new_hire.language)
    subject = _("A task has been assigned to you!")
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": _("This is about task: %(title)s for %(new_hire)s")
                % {"title": admin_task.name, "new_hire": admin_task.new_hire.full_name},
            },
        }
    ]
    if admin_task.comment.exists():
        content.append(
            {
                "type": "quote",
                "data": {
                    "text": "<strong>"
                    + _("Last message: ")
                    + "</strong><br />"
                    + admin_task.comment.last().content,
                },
            }
        )
    html_message = org.create_email(
        {"org": org, "content": content, "user": admin_task.new_hire}
    )
    send_email_with_notification(
        created_for=admin_task.assigned_to,
        subject=subject,
        message="",
        to=admin_task.assigned_to.email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_ADMIN_TASK_NEW_ASSIGNED,
    )


def send_email_new_comment(comment):
    org = Organization.object.get()

    # Check if email notifications for admin task comments are enabled
    if not org.email_admin_task_comments:
        return

    translation.activate(comment.admin_task.assigned_to.language)
    subject = _("Someone added something to task: %(task_name)s") % {
        "task_name": comment.admin_task.name
    }
    content = [
        {
            "type": "paragraph",
            "data": {
                "text": _("Hi %(name)s")
                % {"name": comment.admin_task.assigned_to.first_name},
            },
        },
        {
            "type": "paragraph",
            "data": {
                "text": _(
                    "One of your todo items has been updated by someone else. Here "
                    "is the message:"
                ),
            },
        },
        {
            "type": "quote",
            "data": {
                "text": comment.content + "<br />- " + comment.comment_by.full_name,
            },
        },
    ]
    html_message = org.create_email(
        {"org": org, "content": content, "user": comment.admin_task.new_hire}
    )
    send_email_with_notification(
        created_for=comment.admin_task.assigned_to,
        subject=subject,
        message="",
        to=comment.admin_task.assigned_to.email,
        html_message=html_message,
        notification_type=Notification.Type.SENT_EMAIL_ADMIN_TASK_NEW_COMMENT,
    )
