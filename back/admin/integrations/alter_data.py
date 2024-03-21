from django.urls import reverse_lazy
import base64
from django.utils.translation import gettext_lazy as _
from django.template import Context, Template
from django.conf import settings

class Placeholders:
    """
    Placeholders can come from the following places:

    integration.extra_args: extra arguments placed through the initial data form
    user.extra_fields: extra user fields
    """
    def __init__(self, user=None, integration=None):
        self.available_replacements = {}
        self.user = user
        self.integration = integration

        # add extra fields from users
        if self.user is not None:
            self.add_user_extra_fields()

        if integration is not None:
            self.add({"redirect_url": settings.BASE_URL + reverse_lazy(
                "integrations:oauth-callback", args=[integration.id]
            )})
            # add extra fields from integration
            self.available_replacements |= integration.extra_args

    def add_user_extra_fields(self):
        self.user.refresh_from_db()
        self.available_replacements |= self.user.extra_fields

    def add(self, data_to_add: dict) -> None:
        self.available_replacements |= data_to_add

    def replace(self, text: str, sanitize: bool=False) -> str:
        if self.user is not None:
            text_without_placeholders = self.user.personalize(text, self.available_replacements)
        else:
            t = Template(text)
            context = Context(self.available_replacements)
            text_without_placeholders = t.render(context)

        if sanitize:
            return self.sanitize(text_without_placeholders)

        return text_without_placeholders

    def _replacement_keys(self) -> list:
        # only go two levels deep
        keys = []
        for name, value in self.available_replacements.items():
            # fix base64 secret
            if name == "Authorization" and value.startswith("Basic"):
                value = value.replace(
                    base64.b64encode(value.split(" ", 1)[1].encode("ascii")).decode(
                        "ascii"
                    ),
                    "BASE64 ENCODED SECRET",
                )
            keys.append({value: name})
            if isinstance(value, dict):
                for inner_name, inner_value in value.items():
                    keys.append({inner_value: f"{name}.{inner_name}"})

        return keys

    def sanitize(self, text: str):
        for replace_text, ref in self._replacement_keys():
            text = text.replace(
                str(replace_text),
                _("***Secret value for %(name)s***")
                % {"name": ref},
            )

        return text

