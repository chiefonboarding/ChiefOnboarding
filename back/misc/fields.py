import json

from django.db import models
from django.db.models import JSONField
from fernet_fields.fields import EncryptedField

from .models import File


class ContentJSONField(JSONField):
    """
    Custom JSONField renderer. It will update the signed url of the files before
    pushing it to the frontend. Signed urls expire. We will always want to fetch a new
    one, so users don't bump into files that can't be fetched in the editor
    """

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if "blocks" not in value:
            return value

        for block in value["blocks"]:
            if block["type"] in ["attaches", "image"]:
                if "id" in block["data"]["file"]:
                    block["data"]["file"]["url"] = File.objects.get(
                        id=block["data"]["file"]["id"]
                    ).get_url()
                else:
                    block["data"]["title"] = (
                        "File is invalid. Please remove and try again:"
                        + block["data"]["title"]
                    )
        return value


class EncryptedJSONField(EncryptedField, models.JSONField):
    def from_db_value(self, value, expression, connection, *args):
        if value is not None:
            value = bytes(value)
            return self.to_python(json.loads(self.fernet.decrypt(value)))
