import json

from django import template

register = template.Library()


@register.filter(name="parse_to_json")
def parse_to_json(content):
    try:
        return json.loads(content)
    except:
        return content


@register.filter(name="next_still_form")
def next_still_form(content, current_index):
    """
    Check if the next item is still a form or not.
    Returns False if it's at the end of the list.
    """
    try:
        return content["blocks"][int(current_index) + 1]["type"] == "form"
    except:
        return False
