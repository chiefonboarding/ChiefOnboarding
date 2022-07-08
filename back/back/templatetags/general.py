import json
from datetime import timedelta

from django import template
from django.utils import timezone

from organization.models import File

register = template.Library()


@register.filter(name="parse_to_json")
def parse_to_json(content):
    try:
        return json.loads(content)
    except Exception:
        return content


@register.filter(name="full_download_url")
def full_download_url(id):
    if id == "":
        return ""
    return File.objects.get(id=id).get_url()


@register.filter(name="next_still_form")
def next_still_form(content, current_index):
    """
    Check if the next item is still a form or not.
    Returns False if it's at the end of the list.
    """
    try:
        return content["blocks"][int(current_index) + 1]["type"] == "form"
    except Exception:
        return False


@register.filter(name="personalize")
def personalize(text, user):
    """
    Personalizes content based on user props
    """

    return user.personalize(text)


@register.filter(name="new_hire_trigger_date")
def new_hire_trigger_date(condition, new_hire):
    """
    Shows the actual date that the conditio will trigger
    """

    if condition.condition_type == 2:
        return new_hire.start_day - timedelta(days=condition.days)
    else:
        return new_hire.workday_to_datetime(condition.days)


@register.simple_tag
def show_start_card(conditions, idx, new_hire):
    """
    Check if we should show the start card "New hire's start day"
    Only show when the date before is lower then the start day
    and the date after is higher.
    """
    current_date = timezone.now().date()
    start_day = new_hire.start_day
    current_condition = conditions[idx]

    # Return if this date has already past
    if current_date > start_day:
        return False

    try:
        prev_condition = conditions[idx - 1]
    except Exception:
        prev_condition = None

    if (prev_condition is None and current_condition.condition_type == 0) or (
        prev_condition is not None
        and prev_condition.condition_type == 2
        and current_condition.condition_type == 0
    ):
        return True

    return False
