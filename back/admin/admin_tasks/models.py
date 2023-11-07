from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from slack_bot.utils import Slack, actions, button, paragraph
from organization.models import Notification

from .emails import (
    send_email_new_assigned_admin,
    send_email_new_comment,
    send_email_notification_to_external_person,
)


class AminTaskManager(models.Manager):
    def create_admin_task(
        self,
        new_hire,
        assigned_to,
        name,
        option,
        slack_user,
        email,
        date,
        priority,
        pending_admin_task,
        manual_integration,
        comment,
        send_notification,
    ):
        admin_task = AdminTask.objects.create(
            new_hire=new_hire,
            assigned_to=assigned_to,
            name=name,
            option=option,
            slack_user=slack_user,
            email=email,
            date=date,
            priority=priority,
            based_on=pending_admin_task,
            manual_integration=manual_integration,
        )
        AdminTaskComment.objects.create(
            content=comment,
            comment_by=admin_task.assigned_to,
            admin_task=admin_task,
        )
        if send_notification:
            admin_task.send_notification_new_assigned()

        admin_task.send_notification_third_party()

        Notification.objects.create(
            notification_type=Notification.Type.ADDED_ADMIN_TASK,
            extra_text=name,
            created_for=admin_task.assigned_to,
        )


class AdminTask(models.Model):
    class Priority(models.IntegerChoices):
        EMAIL = 1, _("Low")
        MEDIUM = 2, _("Medium")
        HIGH = 3, _("High")

    class Notification(models.IntegerChoices):
        NO = 0, _("No")
        EMAIL = 1, _("Email")
        SLACK = 2, _("Slack")

    new_hire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("New hire"),
        on_delete=models.CASCADE,
        related_name="new_hire_tasks",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Assigned to"),
        on_delete=models.CASCADE,
        related_name="owner",
        blank=True,
        null=True,
    )
    name = models.CharField(verbose_name=_("Name"), max_length=500)
    option = models.IntegerField(
        verbose_name=_("Send email or text to extra user?"),
        choices=Notification.choices,
    )
    slack_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Slack user"),
        on_delete=models.SET_NULL,
        related_name="slack_user",
        blank=True,
        null=True,
    )
    email = models.EmailField(
        verbose_name=_("Email"), max_length=12500, default="", blank=True
    )
    completed = models.BooleanField(verbose_name=_("Completed"), default=False)
    date = models.DateField(verbose_name=_("Date"), blank=True, null=True)
    priority = models.IntegerField(
        verbose_name=_("Priority"), choices=Priority.choices, default=Priority.MEDIUM
    )
    based_on = models.ForeignKey(
        "sequences.PendingAdminTask",
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("If generated through a sequence, then this will be filled"),
    )
    manual_integration = models.ForeignKey(
        "integrations.Integration",
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Only set if generated based on a manual integration."),
    )

    objects = AminTaskManager()

    @property
    def get_icon_template(self):
        return render_to_string("_admin_task_icon.html")

    def send_notification_third_party(self):
        if self.assigned_to is None:
            # Only happens when a sequence adds this with "manager" or "buddy" is
            # choosen option
            return
        if self.option == AdminTask.Notification.EMAIL:
            send_email_notification_to_external_person(self)
        elif self.option == AdminTask.Notification.SLACK:
            blocks = [
                paragraph(
                    _(
                        "%(name_assigned_to)s needs your help with this task:\n*"
                        "%(task_name)s*\n_%(comment)s_"
                    )
                    % {
                        "name_assigned_to": self.assigned_to.full_name,
                        "task_name": self.name,
                        "comment": self.comment.last().content,
                    }
                ),
                actions(
                    [
                        button(
                            text=_("I have completed this"),
                            style="primary",
                            value=str(self.pk),
                            action_id="admin_task:complete",
                        )
                    ]
                ),
            ]
            Slack().send_message(blocks, self.slack_user.slack_user_id)

    def send_notification_new_assigned(self):
        if self.assigned_to is None:
            # Only happens when a sequence adds this with "manager" or "buddy" is
            # choosen option
            return
        if self.assigned_to.has_slack_account:
            comment = ""
            if self.comment.all().exists():
                comment = _("_%(comment)s_\n by _%(name)s_") % {
                    "comment": self.comment.last().content,
                    "name": self.comment.last().comment_by.full_name,
                }

            text = _("You have just been assigned to *%(title)s* for *%(name)s*\n") % {
                "title": self.name,
                "name": self.new_hire.full_name,
            }
            text += comment
            blocks = [
                paragraph(text),
                actions(
                    [
                        button(
                            text=_("I have completed this"),
                            style="primary",
                            value=str(self.pk),
                            action_id="admin_task:complete",
                        )
                    ]
                ),
            ]
            Slack().send_message(
                blocks=blocks,
                channel=self.assigned_to.slack_user_id,
                text=_("New assigned task!"),
            )
        else:
            send_email_new_assigned_admin(self)

    def mark_completed(self):
        from admin.sequences.tasks import process_condition

        self.completed = True
        self.save()

        # Check if we need to register the manual integration
        if self.manual_integration is not None:
            self.manual_integration.register_manual_integration_run(
                self.new_hire
            )

        # Get conditions with this to do item as (part of the) condition
        conditions = self.new_hire.conditions.filter(
            condition_admin_tasks=self.based_on
        )

        for condition in conditions:
            condition_admin_tasks_id = condition.condition_admin_tasks.values_list(
                "id", flat=True
            )

            # Check if all admin to do items have been added to new hire and are
            # completed. If not, then we know it should not be triggered yet
            completed_tasks = AdminTask.objects.filter(
                based_on_id__in=condition_admin_tasks_id,
                new_hire=self.new_hire,
                completed=True,
            )

            # If the amount matches, then we should process it
            if completed_tasks.count() == len(condition_admin_tasks_id):
                # Send notification only if user has a slack account
                process_condition(
                    condition.id, self.new_hire.id, self.new_hire.has_slack_account
                )

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

    def send_notification_new_message(self):
        if self.admin_task.assigned_to != self.comment_by:
            if self.admin_task.assigned_to.has_slack_account:
                blocks = [
                    paragraph(
                        _(
                            "%(name)s added a message to your task:\n*"
                            "%(task_title)s*\n_%(comment)s_"
                        )
                        % {
                            "name": self.comment_by.full_name,
                            "task_title": self.admin_task.name,
                            "comment": self.content,
                        }
                    ),
                    actions(
                        [
                            button(
                                text=_("I have completed this"),
                                style="primary",
                                value=str(self.pk),
                                action_id="admin_task:complete",
                            )
                        ]
                    ),
                ]
                Slack().send_message(blocks, self.admin_task.assigned_to.slack_user_id)
            else:
                send_email_new_comment(self)
