from admin.introductions.models import Introduction
from users.models import User

def get_intro_templates_for_user(*, user: User):
    return Introduction.templates.for_user(user=user)
