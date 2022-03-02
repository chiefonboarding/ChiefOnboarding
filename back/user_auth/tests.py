from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib import auth
from django.urls import reverse

from users.factories import *

from .utils import get_all_urls

# No need to login for those urls
# These are public pages or authentication happens in a different way
WHITELISTED_URLS = [
    "robots.txt",
    "logout/",
    "password/reset_request/",
    "password/reset_request/done/",
    "password/reset_change/<uidb64>/<token>/",
    "password/reset_change/done/",
    "api/slack/bot",
    "api/slack/callback",
    "new_hire/preboarding/",
]

POST_URLS = [
    "sequences/update_item/todo/1/1/",
    "sequences/forms/1/1/",
    "sequences/1/condition/1/",
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email, password, logged_in",
    [
        ("", "", False),
        ("", "strong_pass", False),
        ("user@example.com", "", False),
        ("user@example.com", "invalid_pass", False),
        ("user@example.com", "strong_pass", True),
        ("user@example.com ", "strong_pass", True),
        ("user2@example.com", "strong_pass", False),
        # Test uppercase
        ("USER@example.com", "strong_pass", True),
    ],
)
def test_login_data_validation(email, password, logged_in, client, new_hire_factory):
    new_hire = new_hire_factory(email="user@example.com")
    new_hire.set_password("strong_pass")
    new_hire.save()

    url = reverse("login")
    data = {"username": email, "password": password}
    client.post(url, data=data, follow=True)
    user = auth.get_user(client)
    assert user.is_authenticated == logged_in


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role, redirect_url",
    [
        (0, "/new_hire/todos/"),
        (3, "/new_hire/colleagues/"),
        (1, "/admin/people/"),
        (2, "/admin/people/"),
    ],
)
def test_redirect_after_login(role, redirect_url, client, new_hire_factory):
    new_hire = new_hire_factory(email="user@example.com", role=role)
    new_hire.set_password("strong_pass")
    new_hire.save()

    url = reverse("login")
    data = {"username": new_hire.email, "password": "strong_pass"}
    response = client.post(url, data=data, follow=True)
    user = auth.get_user(client)
    assert user.is_authenticated
    assert redirect_url == response.redirect_chain[-1][0]


@pytest.mark.django_db
def test_credentials_setting(client, new_hire_factory):
    # Start with credentials enabled
    new_hire_factory(email="user@example.com")
    org = Organization.object.get()
    org.credentials_login = True
    org.save()
    response = client.get(reverse("login"))

    # Login form should be here
    assert "id_username" in response.content.decode()
    assert "id_password" in response.content.decode()
    assert "Log in" in response.content.decode()

    # Disable credentials login
    org.credentials_login = False
    org.save()

    # Login form should be gone
    response = client.get(reverse("login"))
    assert "id_username" not in response.content.decode()
    assert "id_password" not in response.content.decode()
    assert "Log in" not in response.content.decode()

    # Posting to login form will result in 404
    response = client.post(
        reverse("login"), data={"username": "test", "password": "test"}
    )
    assert "Not Found" in response.content.decode()


@pytest.mark.django_db
def test_google_login_setting(client, new_hire_factory):
    # Start with credentials enabled
    new_hire_factory(email="user@example.com")
    org = Organization.object.get()
    org.google_login = True
    org.save()
    response = client.get(reverse("login"))

    # Login form should be here
    assert "Log in with Google" in response.content.decode()

    # Disable credentials login
    org.google_login = False
    org.save()

    # Login form should be gone
    response = client.get(reverse("login"))
    assert "Log in with Google" not in response.content.decode()


@pytest.mark.django_db
@patch("pyotp.TOTP.verify", Mock(return_value=False))
def test_MFA_setting_with_valid_totp(client, new_hire_factory):
    # Start with credentials enabled
    new_hire = new_hire_factory(requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    response = client.post(
        reverse("login"),
        data={"username": new_hire.email, "password": "strong_pass"},
        follow=True,
    )

    user = auth.get_user(client)
    # User is logged in, but will fail any user test because of MFA not verified
    assert user.is_authenticated
    # User will be redirect to MFA form
    assert "/mfa/?next=/redirect/" in response.redirect_chain[-1][0]

    # Test going to a random page
    response = client.post(reverse("new_hire:colleagues"), follow=True)
    # User will be redirect to MFA form again
    assert "/mfa/?next=/new_hire/colleagues/" in response.redirect_chain[-1][0]

    # Enter invalid MFA token and redirect back
    response = client.post(reverse("mfa"), {"otp": 223456})
    assert "OTP token was not correct." in response.content.decode()
    assert "Colleagues" not in response.content.decode()


@pytest.mark.django_db
@patch("pyotp.TOTP.verify", Mock(return_value=True))
def test_MFA_setting_with_invalid_totp(client, new_hire_factory):
    # Start with credentials enabled
    new_hire = new_hire_factory(requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    response = client.post(
        reverse("login"),
        data={"username": new_hire.email, "password": "strong_pass"},
        follow=True,
    )

    # Enter valid (faked) MFA token
    response = client.post(reverse("mfa"), {"otp": 123456}, follow=True)

    assert "/new_hire/todos/" in response.redirect_chain[-1][0]

    # Random url to check if MFA persists
    response = client.get(reverse("new_hire:colleagues"), follow=True)
    assert "Colleagues" in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("url", get_all_urls())
def test_authed_view(url, client, new_hire_factory):
    # This test is only here to check that we aren't accidentally exposing any urls to the public
    # (without authentication)
    new_hire = new_hire_factory(requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    # Skip any urls that are meant to be public
    if url in WHITELISTED_URLS:
        return

    # If url contains params placeholders than swap them
    swaps = [
        ["<int:pk>", "1"],
        ["<int:id>", "1"],
        ["<slug:language>", "en"],
        ["<int:type>", "1"],
        ["<slug:type>", "todo"],
        ["<int:condition_pk>", "1"],
        ["<int:template_pk>", "1"],
        ["<int:template_id>", "1"],
        ["<int:sequence_pk>", "1"],
        ["<slug:template_type>", "1"],
        ["<int:condition>", "1"],
        ["<int:chapter>", "1"],
        ["<int:chapter>", "1"],
        ["<int:integration_id>", "1"],
        ["<int:resource_user>", "1"],
    ]
    for placeholder, real_value in swaps:
        url = url.replace(placeholder, real_value)

    # Some urls are only available with POST
    if url in POST_URLS:
        response = client.post("/" + url, follow=True)
    else:
        response = client.get("/" + url, follow=True)

    assert "Log in" in response.content.decode() or "Authentication credentials were not provided." in response.content.decode()

    # Make sure the url also has MFA enabled
    url = reverse("login")
    data = {"username": new_hire.email, "password": "strong_pass"}
    response = client.post(url, data, follow=True)
    assert "/mfa/" in response.redirect_chain[-1][0]
