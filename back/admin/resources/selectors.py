from admin.resources.models import Resource
from users.models import User


def get_resource_templates_for_user(*, user: User):
    return Resource.templates.for_user(user=user)
