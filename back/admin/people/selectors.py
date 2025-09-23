from django.contrib.auth import get_user_model
from django.db.models import Q

from users.models import User


def get_new_hires_for_user(*, user: User):
    if user.is_admin:
        return get_user_model().new_hires.all()
    else:
        return get_user_model().new_hires.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        )


def get_colleagues_for_user(*, user: User):
    if user.is_admin:
        return get_user_model().objects.all()
    else:
        return get_user_model().objects.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        )


def get_offboarding_colleagues_for_user(*, user: User):
    if user.is_admin:
        return get_user_model().offboarding.all()
    else:
        return get_user_model().offboarding.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        )
