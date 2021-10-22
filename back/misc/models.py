import json
import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .s3 import S3
from .urlparser import URLParser

CONTENT_OPTIONS = (
    ("p", "p"),
    ("h1", "h1"),
    ("h2", "h2"),
    ("h3", "h3"),
    ("quote", "quote"),
    ("youtube", "youtube"),
    ("ul", "ul"),
    ("ol", "ol"),
    ("hr", "hr"),
    ("file", "file"),
    ("image", "image"),
    ("video", "video"),
    ("question", "question"),
)


class File(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, blank=True)
    ext = models.CharField(max_length=10)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def get_url(self):
        return S3().get_file(self.key)


@receiver(pre_delete, sender=File)
def remove_file(sender, instance, **kwargs):
    S3().delete_file(instance.key)


class Content(models.Model):
    type = models.CharField(choices=CONTENT_OPTIONS, max_length=100)
    items = models.JSONField(models.TextField(blank=True), default=list)
    content = models.TextField(blank=True)
    files = models.ManyToManyField(File)

    # for courses
    answer = models.TextField(blank=True)

    def to_slack_block(self, user):
        replacements = (
            ("<p>", ""),
            ("</p>", ""),
            ("<br>", ""),
            ("<br />", ""),
            ("<b>", "*"),
            ("</b>", "*"),
            ("<strong>", "*"),
            ("</strong>", "*"),
            ("</i>", "_"),
            ("<i>", "_"),
            ("<em>", "_"),
            ("</em>", "_"),
            ("<u>", ""),
            ("</u>", ""),
            ("<code>", "`"),
            ("</code>", "`"),
            ("</strike>", "~"),
            ("<strike>", "~"),
        )
        content = user.personalize(self.content)
        for r in replacements:
            content = content.replace(*r)
        parser = URLParser()
        parser.feed(content)
        for i in parser.get_links():
            content = content.replace(
                i["original_tag"] + i["text"] + "</a>",
                "<" + i["url"] + "|" + i["text"] + ">",
            )
        if content == "":
            content = "-"
        text = {"type": "section", "text": {"type": "mrkdwn", "text": content}}
        if self.type == "h1" or self.type == "h2" or self.type == "h3":
            text["text"]["text"] = "*" + content + "*"
        elif self.type == "quote":
            return {
                "type": "context",
                "elements": {"text": {"type": "mrkdwn", "text": content}},
            }
            text["type"] = "context"
        elif self.type == "ul":
            ul_list = ""
            for idx, val in enumerate(self.items):
                ul_list += str(idx + 1) + ". " + user.personalize(val["content"]) + "\n"
            text["text"]["text"] = ul_list
        elif self.type == "ol":
            ol_list = ""
            for val in self.items:
                ol_list += "* " + user.personalize(val["content"]) + "\n"
            text["text"]["text"] = ol_list
        elif self.type == "hr":
            return {"type": "divider"}
        elif self.type == "file":
            files_text = "<" + self.files[0].get_url() + "|Watch video>"
            text["text"]["text"] = files_text
        elif self.type == "video":
            files_text = ""
            for i in self.files.all():
                files_text += "<" + i.get_url() + "|" + i.name + "> "
            text["text"]["text"] = files_text
        elif self.type == "image":
            return {
                "type": "image",
                "image_url": self.files.first().get_url(),
                "alt_text": "image",
            }
        elif self.type == "question":
            options = []
            for i in self.items:
                options.append(
                    {
                        "text": {
                            "type": "plain_text",
                            "text": user.personalize(i["text"]),
                            "emoji": True,
                        },
                        "value": i["id"],
                    }
                )
            return {
                "type": "input",
                "block_id": str(self.id),
                "element": {
                    "type": "static_select",
                    "action_id": str(self.id),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select answer",
                        "emoji": True,
                    },
                    "options": options,
                },
                "label": {"type": "plain_text", "text": content, "emoji": True},
            }

        return text
