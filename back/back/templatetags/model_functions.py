from django import template

register = template.Library()


@register.simple_tag
def get_user_answer_by_chapter(resource_user, chapter, idx):
    # Yes this is ugly and expensive. Yes, this needs to be rewritten
    user_given_answer = resource_user.get_user_answer_by_chapter(chapter).answers[
        f"item-{idx}"
    ]
    questions = chapter.content["blocks"]
    for question in questions:
        for option in question["items"]:
            if option["id"] == user_given_answer:
                return option["text"]
    return "Could not find answer"
