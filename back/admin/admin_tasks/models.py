from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from slack_bot.slack import Slack

from .emails import send_email_new_assigned_admin, send_email_new_comment, send_email_notification_to_external_person

PRIORITY_CHOICES = ((1, _("Low")), (2, _("Medium")), (3, _("High")))

NOTIFICATION_CHOICES = ((0, _("No")), (1, _("Email")), (2, _("Slack")))


class AdminTask(models.Model):
    new_hire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="new_hire_tasks",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=500)
    option = models.IntegerField(choices=NOTIFICATION_CHOICES)
    slack_user = models.CharField(max_length=12500, default="", blank=True)
    email = models.EmailField(max_length=12500, default="", blank=True)
    completed = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    def save(self, *args, **kwargs):
        # checking if this is new before saving, sending information after we have the ID.
        is_new = self.pk is None
        super(AdminTask, self).save(*args, **kwargs)
        if is_new and self.option == 1:
            # through email
            send_email_notification_to_external_person(self)
        elif is_new and self.option == 2:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.assigned_to.full_name()
                        + " needs your help with this task:\n*"
                        + self.title
                        + "*\n_"
                        + self.comment.last().content
                        + "_",
                    },
                },
                {
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": "I have completed this",
                                },
                                "style": "primary",
                                "value": "admin_task:complete:" + self.pk,
                            }
                        ],
                    }
                },
            ]
            s = Slack()
            s.send_message(channel=self.slack_user, blocks=blocks)

    def send_notification_new_assigned(self):
        if self.assigned_to.slack_user_id is not None:
            s = Slack()
            comment = ""
            if self.comment.all().exists():
                comment = "_" + self.comment.last() + "\n by " + self.comment.last().comment_by.full_name() + "_"
            text = f"You have just been assigned to *{self.title}* for *{self.new_hire.full_name()}\n{comment}"

            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": comment}},
                {
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": "I have completed this",
                                },
                                "style": "primary",
                                "value": "admin_task:complete:" + self.pk,
                            }
                        ],
                    }
                },
            ]
        else:
            send_email_new_assigned_admin(self)


class AdminTaskComment(models.Model):
    admin_task = models.ForeignKey("AdminTask", on_delete=models.CASCADE, related_name="comment")
    content = models.CharField(max_length=12500)
    date = models.DateTimeField(auto_now_add=True)
    comment_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def send_notification_new_message(self, team):
        if self.admin_task.assigned_to != self.comment_by:
            if self.admin_task.assigned_to.slack_user_id != "" and team is not None:
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self.comment_by.full_name()
                            + " added a message to your task:\n*"
                            + self.admin_task.title
                            + "*\n_"
                            + self.comment
                            + "_",
                        },
                    },
                    {
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "emoji": True,
                                        "text": "I have completed this",
                                    },
                                    "style": "primary",
                                    "value": "admin_task:complete:" + self.pk,
                                }
                            ],
                        }
                    },
                ]
                s = Slack()
                s.send_message(channel=self.slack_user, blocks=blocks)
            else:
                send_email_new_comment(self)
