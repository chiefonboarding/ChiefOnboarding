from django.utils.translation import gettext as _

from admin.badges.models import Badge
from admin.resources.models import Resource
from admin.to_do.models import ToDo
from organization.models import Organization
from organization.utils import send_email_with_notification


def send_sequence_message(new_hire, admin, message, subject):
    # used to send custom external messages to anyone
    org = Organization.object.get()
    html_message = org.create_email({"org": org, "content": message, "user": new_hire})
    send_email_with_notification(
        subject=subject,
        message="",
        to=admin.email,
        created_for=admin,
        html_message=html_message,
        notification_type="sent_email_custom_sequence",
    )


def send_sequence_update_message(all_notifications, new_hire):
    # used to send updates to new hires based on things that got assigned to them
    org = Organization.object.get()
    subject = _("Here is an update!")
    blocks = []

    notifications = all_notifications.filter(notification_type="added_todo")
    if notifications.exists():
        blocks.append(
            {
                "type": "paragraph",
                "data": {
                    "text": _("Todo item")
                    if notifications.count() == 1
                    else _("Todo items")
                },
            }
        )
        text = ""
        for to_do in ToDo.objects.filter(
            id__in=notifications.values_list("item_id", flat=True)
        ):
            text += f"- {to_do.name} <br />"
        blocks.append({"type": "quote", "data": {"text": text}})

    notifications = all_notifications.filter(notification_type="added_resource")
    if notifications.exists():
        blocks.append(
            {
                "type": "paragraph",
                "data": {
                    "text": _("Resource")
                    if notifications.count() == 1
                    else _("Resources")
                },
            }
        )
        text = ""
        for i in Resource.objects.filter(
            id__in=notifications.values_list("item_id", flat=True)
        ):
            text += f"- {i.name} <br />"
        blocks.append({"type": "quote", "data": {"text": text}})

    notifications = all_notifications.filter(notification_type="added_badge")
    if notifications.exists():
        blocks.append(
            {
                "type": "paragraph",
                "data": {
                    "text": _("Badge") if notifications.count() == 1 else _("Badges")
                },
            }
        )
        text = ""
        for i in Badge.objects.filter(
            id__in=notifications.values_list("item_id", flat=True)
        ):
            text += f"- {i.name} <br />"
        blocks.append({"type": "quote", "data": {"text": text}})

    html_message = org.create_email({"org": org, "content": blocks, "user": new_hire})
    send_email_with_notification(
        subject=subject,
        message="",
        to=new_hire.email,
        created_for=new_hire,
        html_message=html_message,
        notification_type="sent_email_new_hire_with_updates",
    )
