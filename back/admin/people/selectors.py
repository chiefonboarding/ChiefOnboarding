from django.db.models import Q

from users.models import User


def get_new_hires_for_user(*, user: User):
    if user.is_admin:
        return User.new_hires.all()
    else:
        return User.new_hires.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()


def get_colleagues_for_user(*, user: User):
    if user.is_admin:
        return User.objects.all()
    else:
        return User.objects.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()


def get_offboarding_colleagues_for_user(*, user: User):
    if user.is_admin:
        return User.offboarding.all()
    else:
        return User.offboarding.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()
