import pytest
from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user_model
from django.test import override_settings

from .adapter import SocialAccountAdapter


@pytest.mark.django_db
@override_settings(OIDC_ROLE_ADMIN_PATTERN="^Administrators.*")
@override_settings(OIDC_ROLE_MANAGER_PATTERN="^Manager.*")
@override_settings(OIDC_ROLE_NEW_HIRE_PATTERN="^Newhire.*")
def test_get_user_role():
    assert (
        SocialAccountAdapter()._get_user_role("Administrators test")
        == get_user_model().Role.ADMIN
    )
    assert (
        SocialAccountAdapter()._get_user_role("Manager test")
        == get_user_model().Role.MANAGER
    )
    assert (
        SocialAccountAdapter()._get_user_role("Newhire test")
        == get_user_model().Role.NEWHIRE
    )

    # intentional typo
    assert (
        SocialAccountAdapter()._get_user_role("Maanager test")
        == get_user_model().Role.OTHER
    )


@pytest.mark.django_db
@override_settings(OIDC_ROLE_ADMIN_PATTERN="^Administrators.*")
@override_settings(OIDC_ROLE_MANAGER_PATTERN="^Manager.*")
@override_settings(OIDC_ROLE_NEW_HIRE_PATTERN="^Newhire.*")
@override_settings(OIDC_ROLE_PATH_IN_RETURN="details.zoneinfo")
def test_populate_user(employee_factory):
    employee = employee_factory()
    sociallogin = SocialLogin(user=employee)

    data = {
        "first_name": "John",
        "last_name": "Do",
        "email": "John@chiefonboarding.com",
        "username": "john@chiefonboarding.com",
        "details": {"zoneinfo": "Administrators test"},
    }
    user = SocialAccountAdapter().populate_user(None, sociallogin, data)
    # saving happens elsewhere, so force save here
    user.save()
    assert get_user_model().objects.count() == 1
    assert get_user_model().objects.first().role == get_user_model().Role.ADMIN
