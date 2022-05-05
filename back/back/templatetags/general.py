import json

from django import template

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
