import pytest
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.openid_connect.provider import (
    OpenIDConnectProvider,
)
from django.contrib.auth import get_user_model
from django.test import override_settings

from .adapter import SocialAccountAdapter


def _ensure_provider_registered(provider_id: str, provider_class):
    """
    Register a provider if not already registered.

    Necessary as "django-allauth" initializes the registry before the
    `@override_settings` decorator is applied.
    """
    from allauth.socialaccount.providers import registry

    if not registry.provider_map.get(provider_id):
        registry.register(provider_class)


@pytest.fixture
def register_google_provider():
    _ensure_provider_registered("google", GoogleProvider)
    yield


@pytest.fixture
def register_openid_connect_provider():
    _ensure_provider_registered("openid_connect", OpenIDConnectProvider)
    yield


@pytest.mark.django_db
@override_settings(OIDC_ROLE_ADMIN_PATTERN="^Administrators.*")
@override_settings(OIDC_ROLE_MANAGER_PATTERN="^Manager.*")
@override_settings(OIDC_ROLE_NEW_HIRE_PATTERN="^Newhire.*")
def test_get_user_role():
    assert (
        SocialAccountAdapter()._get_user_role(["Administrators test"])
        == get_user_model().Role.ADMIN
    )
    assert (
        SocialAccountAdapter()._get_user_role(["Manager test"])
        == get_user_model().Role.MANAGER
    )
    assert (
        SocialAccountAdapter()._get_user_role(["Newhire test"])
        == get_user_model().Role.NEWHIRE
    )

    # intentional typo
    assert (
        SocialAccountAdapter()._get_user_role(["Maanager test"])
        == get_user_model().Role.OTHER
    )


@pytest.mark.django_db
@override_settings(OIDC_ROLE_ADMIN_PATTERN="^Administrators.*")
@override_settings(OIDC_ROLE_MANAGER_PATTERN="^Manager.*")
@override_settings(OIDC_ROLE_NEW_HIRE_PATTERN="^Newhire.*")
@override_settings(OIDC_ROLE_PATH_IN_RETURN="details.zoneinfo")
@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "openid_connect": {
            "APPS": [
                {
                    "provider_id": "test-server",
                    "name": "Test Server",
                    "client_id": "test-client-id",
                    "secret": "test-secret",
                }
            ]
        }
    },
)
def test_populate_user(employee_factory, register_openid_connect_provider):
    employee = employee_factory()
    account = SocialAccount(
        user=employee,
        extra_data={
            "id_token": {
                "first_name": "John",
                "last_name": "Do",
                "email": "John@chiefonboarding.com",
                "username": "john@chiefonboarding.com",
                "details": {"zoneinfo": "Administrators test"},
            }
        },
    )
    sociallogin = SocialLogin(user=employee, account=account)

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


@pytest.mark.django_db
@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "google": {
            "APPS": [
                {
                    "client_id": "test-client-id",
                    "secret": "test-secret",
                    "key": "dummy",
                }
            ],
            "AUTH_PARAMS": {
                "access_type": "offline",
            },
            "OAUTH_PKCE_ENABLED": True,
        }
    }
)
def test_populate_google_user(employee_factory, register_google_provider):
    employee = employee_factory()
    account = SocialAccount(
        user=employee,
        # See: https://openid.net/specs/openid-connect-core-1_0.html#IDToken
        extra_data={
            "iss": "https://accounts.google.com",
            "azp": "123456789012-0e3b215c34faf2828d7bb66b5f24e992.apps.googleusercontent.com",
            "aud": "123456789012-0e3b215c34faf2828d7bb66b5f24e992.apps.googleusercontent.com",
            "sub": "123456789012345678901",
            "hd": "chiefonboarding.com",
            "email": "John@chiefonboarding.com",
            "email_verified": True,
            "at_hash": "-someHASH",
            "name": "John Do",
            "picture": "https://lh3.googleusercontent.com/a/...",
            "given_name": "John",
            "family_name": "Do",
            "iat": 1763729550,
            "exp": 1763733150,
        },
    )
    sociallogin = SocialLogin(user=employee, account=account)

    data = {
        "first_name": "John",
        "last_name": "Do",
        "email": "John@chiefonboarding.com",
    }
    user = SocialAccountAdapter().populate_user(None, sociallogin, data)
    # saving happens elsewhere, so force save here
    user.save()
    assert get_user_model().objects.count() == 1
    # unlike `test_populate_user`, no role information is present in our data
    assert get_user_model().objects.first().role == get_user_model().Role.OTHER
