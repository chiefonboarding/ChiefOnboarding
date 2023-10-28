import hashlib
import json
from datetime import timedelta

from django import template
from django.utils import timezone

from admin.sequences.models import Condition
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
    Shows the actual date that the condition will trigger
    """

    if condition.condition_type == Condition.Type.BEFORE:
        return new_hire.start_day - timedelta(days=condition.days)
    else:
        return new_hire.workday_to_datetime(condition.days)

@register.filter(name="offboarding_trigger_date")
def offboarding_trigger_date(condition, employee):
    """
    Shows the actual date that the condition will trigger
    """
    return employee.termination_date - timedelta(days=condition.days)


@register.simple_tag
def show_highlighted_date_card(conditions, idx, highlighted_date):
    """
    Check if we should show the start/termination card
    Only show when the date before is lower then the start day
    and the date after is higher.
    """
    current_date = timezone.now().date()
    current_condition = conditions[idx]

    # Return if this date has already past
    if current_date > highlighted_date:
        return False

    try:
        prev_condition = conditions[idx - 1]
    except Exception:
        prev_condition = None

    if (
        prev_condition is None
        and current_condition.condition_type == Condition.Type.AFTER
    ) or (
        prev_condition is not None
        and prev_condition.condition_type == Condition.Type.BEFORE
        and current_condition.condition_type == Condition.Type.AFTER
    ):
        return True

    return False


@register.filter(name="hash")
def hash(text):
    """
    Hashes the value. Could be used to get uuids (for data that is unique).
    """
    text = text.encode()
    return hashlib.sha256(text).hexdigest()
