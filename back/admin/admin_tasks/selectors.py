from admin.admin_tasks.models import AdminTask
from users.models import User


def get_admin_tasks_for_department(*, user: User):
    return AdminTask.objects.for_user(user=user)


def get_admin_tasks_for_user(*, user: User):
    return AdminTask.objects.filter(assigned_to=user)
