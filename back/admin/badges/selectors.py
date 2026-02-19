from admin.badges.models import Badge
from users.models import User


def get_badge_templates_for_user(*, user: User):
    return Badge.templates.for_user(user=user)
