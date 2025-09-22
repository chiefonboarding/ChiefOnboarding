from admin.hardware.models import Hardware
from users.models import User

def get_hardware_templates_for_user(*, user: User):
    return Hardware.templates.for_user(user=user)
