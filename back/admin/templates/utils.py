from django.apps import apps

from admin.appointments.forms import AppointmentForm
from admin.badges.forms import BadgeForm
from admin.introductions.forms import IntroductionForm
from admin.preboarding.forms import PreboardingForm
from admin.resources.forms import ResourceForm
from admin.to_do.forms import ToDoForm
from admin.hardware.forms import HardwareForm

MODELS = [
    {"app": "to_do", "model": "ToDo", "user_field": "to_do", "form": ToDoForm},
    {
        "app": "resources",
        "model": "Resource",
        "user_field": "resources",
        "form": ResourceForm,
    },
    {
        "app": "introductions",
        "model": "Introduction",
        "user_field": "introductions",
        "form": IntroductionForm,
    },
    {
        "app": "appointments",
        "model": "Appointment",
        "user_field": "appointments",
        "form": AppointmentForm,
    },
    {
        "app": "preboarding",
        "model": "Preboarding",
        "user_field": "preboarding",
        "form": PreboardingForm,
    },
    {"app": "badges", "model": "Badge", "user_field": "badges", "form": BadgeForm},
    {
        "app": "hardware",
        "model": "Hardware",
        "user_field": "hardware",
        "form": HardwareForm,
    },
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
