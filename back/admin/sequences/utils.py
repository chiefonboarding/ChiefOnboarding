from django.apps import apps

from admin.badges.forms import BadgeForm
from admin.templates.utils import MODELS

MODELS += [
    {"app": "sequences", "model": "PendingTextMessage", "form": BadgeForm},
    {"app": "sequences", "model": "PendingEmailMessage", "form": BadgeForm},
    {"app": "sequences", "model": "PendingSlackMessage", "form": BadgeForm},
    {"app": "sequences", "model": "PendingAdminTask", "form": BadgeForm},
    {"app": "sequences", "model": "AccountProvision", "form": BadgeForm},
]


def template_model_exists(template_slug):
    return any([x["model"].lower() == template_slug.lower() for x in MODELS])


def get_templates_model(template_slug):
    if template_model_exists(template_slug):
        model_item = next(
            (x for x in MODELS if x["model"].lower() == template_slug.lower()), None
        )
        return apps.get_model(model_item["app"], model_item["model"])


def get_user_field(template_slug):
    if template_model_exists(template_slug):
        return next(
            (
                x["user_field"]
                for x in MODELS
                if x["model"].lower() == template_slug.lower()
            ),
            None,
        )


def get_model_item(template_slug):
    model_item = None
    if template_model_exists(template_slug):
        model_item = next(
            (x for x in MODELS if x["model"].lower() == template_slug.lower()), None
        )
    return model_item


def get_model_form(template_slug):
    model = get_model_item(template_slug)

    if model is None:
        return None

    return get_model_item(template_slug)["form"]
