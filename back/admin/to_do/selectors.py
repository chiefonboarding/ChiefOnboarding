from admin.to_do.models import ToDo
from users.models import User

def get_to_do_templates_for_user(*, user: User):
    return ToDo.templates.for_user(user=user)
