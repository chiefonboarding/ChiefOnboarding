from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from misc.fields import ContentJSONField
from organization.models import BaseItem


class ToDo(BaseItem):
    content = ContentJSONField(default=dict, verbose_name=_("Content"))
    due_on_day = models.IntegerField(verbose_name=_("Due on day"), default=0)
    # Chat bot specific actions
    send_back = models.BooleanField(
        verbose_name=_(
            "Post new hire's answers from form (if applicable) back to Slack channel"
        ),
        default=False,
    )
    slack_channel = models.ForeignKey(
        "slack_bot.SlackChannel",
        verbose_name=_("Slack channel"),
        null=True,
        on_delete=models.SET_NULL,
    )

    @property
    def get_icon_template(self):
        return render_to_string("_todo_icon.html")

    @property
    def notification_add_type(self):
        return "added_todo"

    @property
    def update_url(self):
        return reverse("todo:update", args=[self.id])

    @property
    def delete_url(self):
        return reverse("todo:delete", args=[self.id])

    @property
    def inline_slack_form(self):
        valid = True
        blocks = self.content["blocks"]
        for i in blocks:
            if "data" in i and "type" in i["data"] and i["data"]["type"] in ["check", "upload"]:
                valid = False
                break
        return valid
