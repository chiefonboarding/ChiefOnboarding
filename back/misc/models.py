from django.contrib.postgres.fields import JSONField
from django.db import models
import uuid

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .s3 import S3
import json

CONTENT_OPTIONS = (
    ('p', 'p'),
    ('h1', 'h1'),
    ('h2', 'h2'),
    ('h3', 'h3'),
    ('quote', 'quote'),
    ('youtube', 'youtube'),
    ('ul', 'ul'),
    ('ol', 'ol'),
    ('hr', 'hr'),
    ('file', 'file'),
    ('image', 'image'),
    ('question', 'question')
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
    items = JSONField(models.CharField(max_length=100000), default=list)
    content = models.CharField(max_length=100000, blank=True)
    files = models.ManyToManyField(File)

    # for courses
    answer = models.CharField(max_length=10000, blank=True)

    def to_slack_block(self):
        content = self.content.replace('<p>', '').replace('</p>', '').replace('<br>', '')
        text = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": content
            }
        }
        if self.type == 'h1' or self.type == 'h2' or self.type == 'h3':
            text['text']['text'] = '*' + content + '*'
        elif self.type == 'quote':
            text['type'] = 'context'
        elif self.type == 'ul':
            ul_list = ''
            for idx, val in enumerate(self.items):
                ul_list += str(idx + 1) + '. ' + val['content'] + '\n'
            text['text']['text'] = ul_list
        elif self.type == 'ol':
            ol_list = ''
            for val in self.items:
                ol_list += '* ' + val['content'] + '\n'
            text['text']['text'] = ol_list
        elif self.type == 'hr':
            return {"type": "divider"}
        elif self.type == 'file':
            files_text = ''
            for i in self.files.all():
                files_text += '<' + i.get_url() + '|' + i.name + '> '
            text['text']['text'] = files_text
        elif self.type == 'image':
            return {
                "type": "image",
                "image_url": self.files.first().get_url(),
                "alt_text": 'image'
            }
        elif self.type == 'question':
            options = []
            for i in self.items:
                options.append({
                    "text": {
                        "type": "plain_text",
                        "text": i['text'],
                        "emoji": True
                    },
                    "value": i['id']
                })
            return {
                "type": "input",
                "block_id": str(self.id),
                "element": {
                    "type": "static_select",
                    "action_id": str(self.id),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select answer",
                        "emoji": True
                    },
                    "options": options
                },
                "label": {
                    "type": "plain_text",
                    "text": content,
                    "emoji": True
                }
            }

        return text
