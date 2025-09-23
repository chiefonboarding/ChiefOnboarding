from django.contrib.auth import get_user_model
from django.db.models import Q


def get_available_departments_for_user(*, user):
    from users.models import Department

    if user.is_admin:
        return Department.objects.all()
    else:
        return user.departments.all()


def get_departments_query(*, user):
    from users.models import Department

    if user.is_admin:
        deps = Department.objects.all()
    else:
        deps = user.departments.all()
    return Q(departments__isnull=True) | Q(departments__in=deps)


def get_all_managers_and_admins_for_departments_of_user(*, user):
    return get_user_model().managers_and_admins.filter(get_departments_query(user=user))


def get_all_new_hires_for_departments_of_user(*, user):
    return get_user_model().new_hires.filter(get_departments_query(user=user))


def get_all_managers_and_admins_for_departments_of_user_with_slack(*, user):
    return (
        get_user_model()
        .managers_and_admins.with_slack()
        .filter(get_departments_query(user=user))
    )


def get_all_offboarding_users_for_departments_of_user(*, user):
    return get_user_model().offboarding.filter(get_departments_query(user=user))
