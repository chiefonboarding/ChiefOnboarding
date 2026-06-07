from admin.preboarding.models import Preboarding
from users.models import User


def get_preboarding_templates_for_user(*, user: User):
    return Preboarding.templates.for_user(user=user)
