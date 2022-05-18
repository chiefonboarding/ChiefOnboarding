from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag
def get_user_answer_by_chapter(resource_user, chapter, idx):
    # Yes this is ugly and expensive. Yes, this needs to be rewritten
    user_answer = resource_user.get_user_answer_by_chapter(chapter)
    if user_answer is None:
        return _("N/A")
    user_given_answer = resource_user.get_user_answer_by_chapter(chapter).answers[
        f"item-{idx}"
    ]
    questions = chapter.content["blocks"]
    for question in questions:
        for option in question["items"]:
            if option["id"] == user_given_answer:
                return option["text"]
    return _("Could not find answer")
