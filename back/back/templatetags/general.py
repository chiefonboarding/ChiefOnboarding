import json

from django import template

register = template.Library()


@register.filter(name="parse_to_json")
def parse_to_json(content):
    try:
        return json.loads(content)
    except:
        return content
