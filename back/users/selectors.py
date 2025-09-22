from django.contrib.auth import get_user_model

def get_available_departments_for_user(*, user):
    from users.models import Department

    if user.is_admin:
        return Department.objects.all()
    return user.departments.all()

def get_all_managers_and_admins_for_departments_of_user(*, user):
    departments = get_available_departments_for_user(user=user)
    return get_user_model().managers_and_admins.filter(departments__in=departments)

def get_all_new_hires_for_departments_of_user(*, user):
    departments = get_available_departments_for_user(user=user)
    return get_user_model().new_hires.filter(departments__in=departments)


def get_all_managers_and_admins_for_departments_of_user_with_slack(*, user):
    departments = get_available_departments_for_user(user=user)
    return get_user_model().managers_and_admins.with_slack().filter(departments__in=departments)
