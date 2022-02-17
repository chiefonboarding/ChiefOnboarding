from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from slack_bot.slack import Slack

from .emails import (
    send_email_new_assigned_admin,
    send_email_new_comment,
    send_email_notification_to_external_person,
)

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

    @property
    def get_icon_template(self):
        return render_to_string("_admin_task_icon.html")

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
                        "text": _("%(name_assigned_to) needs your help with this task:\n*%(task_name)*\n_%(comment)_") % {'name_assigned_to': self.assigned_to.full_name(), 'task_name': self.title, 'comment': self.comment.last().content}
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
                                    "text": _("I have completed this"),
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
        if self.assigned_to.has_slack_account:
            s = Slack()
            comment = ""
            if self.comment.all().exists():
                comment = _("_%(comment)\n by %(name)_") % {'comment':self.comment.last(), 'name':self.comment.last().comment_by.full_name() }

            text = _("You have just been assigned to *%(title)* for *%(name)\n%(comment)") % {'title': self.title, 'name': self.new_hire.full_name(), 'comment': comment}

            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": text}},
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
            s.send_message(channel=self.slack_user, blocks=blocks)
        else:
            send_email_new_assigned_admin(self)

    class Meta:
        ordering = ["completed", "date"]


class AdminTaskComment(models.Model):
    admin_task = models.ForeignKey(
        "AdminTask", on_delete=models.CASCADE, related_name="comment"
    )
    content = models.CharField(max_length=12500)
    date = models.DateTimeField(auto_now_add=True)
    comment_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date"]

    def send_notification_new_message(self, team):
        if self.admin_task.assigned_to != self.comment_by:
            if self.admin_task.assigned_to.has_slack_account and team is not None:
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": _("%(name) added a message to your task:\n*%(task_title)*\n_%(comment)_") % {'name': self.comment_by.full_name, 'title': self.admin_task.title, 'comment':self.comment}
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
                                        "text": _("I have completed this"),
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
