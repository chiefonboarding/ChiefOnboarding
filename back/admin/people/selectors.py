from django.db.models import Q

from users.models import User


def get_new_hires_for_user(*, user: User):
    if user.is_admin:
        return User.new_hires.all()
    elif user.is_manager:
        return User.new_hires.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()
    return user.objects.none()


def get_colleagues_for_user(*, user: User):
    if user.is_admin:
        return User.objects.all()
    elif user.is_manager:
        return User.objects.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()
    return User.objects.none()


def get_offboarding_colleagues_for_user(*, user: User):
    if user.is_admin:
        return User.offboarding.all()
    elif user.is_manager:
        return User.offboarding.filter(
            Q(departments__isnull=True) | Q(departments__in=user.departments.all())
        ).distinct()
    return User.objects.none()
