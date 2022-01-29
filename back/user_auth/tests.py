import pytest
from django.urls import reverse

from users.factories import *
from django.contrib import auth
from unittest.mock import Mock, patch


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
    data = {"username": new_hire.email, "password": "strong_pass" }
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
    response = client.post(reverse("login"), data={"username": "test", "password": "test"})
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
@patch('pyotp.TOTP.verify', Mock(return_value=False))
def test_MFA_setting(client, new_hire_factory):
    # Start with credentials enabled
    new_hire = new_hire_factory(email="user@example.com", requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    response = client.post(reverse("login"), data={"username": new_hire.email, "password": "strong_pass"}, follow=True)

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
    response = client.post(reverse("mfa"), {"otp": 223456}, follow=True)
    assert "OTP token was not correct." in response.content.decode()
    assert "/mfa/?next=/new_hire/colleagues/" in response.redirect_chain[-1][0]


@pytest.mark.django_db
@patch('pyotp.TOTP.verify', Mock(return_value=True))
def test_MFA_setting(client, new_hire_factory):
    # Start with credentials enabled
    new_hire = new_hire_factory(email="user@example.com", requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    response = client.post(reverse("login"), data={"username": new_hire.email, "password": "strong_pass"}, follow=True)

    # Enter valid (faked) MFA token
    response = client.post(reverse("mfa"), {"otp": 123456}, follow=True)

    assert "/new_hire/todos/" in response.redirect_chain[-1][0]

    # Random url to check if MFA persists
    response = client.post(reverse("new_hire:colleagues"), follow=True)
    assert "Colleagues" in response.content.decode()

