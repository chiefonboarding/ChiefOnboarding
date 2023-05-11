from unittest.mock import Mock, patch

import pytest
from django.contrib import auth
from django.urls import reverse

from organization.models import Organization

from .utils import get_all_urls

# No need to login for those urls
# These are public pages or authentication happens in a different way
WHITELISTED_URLS = [
    "robots.txt",
    "logout/",
    "google/",
    "api/auth/google_login",
    "api/auth/oidc_login/",
    "password/reset_request/",
    "password/reset_request/done/",
    "password/reset_change/<uidb64>/<token>/",
    "password/reset_change/done/",
    "api/slack/bot",
    "new_hire/preboarding/",
    "new_hire/slackform/<int:pk>/",
    "setup/",
    "login/",
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
def test_google_login_setting(client, new_hire_factory, integration_factory):
    # Start with credentials enabled
    new_hire_factory(email="user@example.com")
    integration_factory(integration=3)

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
def test_oidc_login_setting(client, new_hire_factory, settings):
    # Start with credentials enabled
    new_hire_factory(email="user@example.com")

    org = Organization.object.get()
    org.oidc_login = True
    org.save()
    response = client.get(reverse("login"))
    # make sure the login form is there
    settings.OIDC_FORCE_AUTHN = False
    # Login form should be here
    login_name = "Log in with " + settings.OIDC_LOGIN_DISPLAY
    assert login_name in response.content.decode()

    # Disable credentials login
    org.oidc_login = False
    org.save()

    # Login form should be gone
    response = client.get(reverse("login"))
    assert login_name not in response.content.decode()


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
@patch("pyotp.TOTP.verify", Mock(return_value=False))
def test_MFA_setting_with_recovery_key(client, new_hire_factory):
    new_hire = new_hire_factory(requires_otp=True)
    new_hire.set_password("strong_pass")
    new_hire.save()

    # Reset OTP keys so we have fresh ones
    otp_keys = new_hire.reset_otp_recovery_keys()

    response = client.post(
        reverse("login"),
        data={"username": new_hire.email, "password": "strong_pass"},
        follow=True,
    )

    # Enter invalid MFA token and redirect back
    response = client.post(reverse("mfa"), {"otp": 223456}, follow=True)
    assert "OTP token was not correct." in response.content.decode()

    # Test with recovery key instead
    response = client.post(reverse("mfa"), {"otp": otp_keys[0]}, follow=True)
    assert "OTP token was not correct." not in response.content.decode()
    assert "Colleagues" in response.content.decode()

    new_hire.refresh_from_db()

    assert not new_hire.requires_otp


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
    # This test is only here to check that we aren't accidentally exposing any urls to
    # the public (without authentication)
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
        ["<int:condition>", "1"],
        ["<int:exists>", "1"],
        ["<uuid:uuid>", "65a6d9b5-6e1d-47de-b677-8c4e73bf3f00"],
    ]
    for placeholder, real_value in swaps:
        url = url.replace(placeholder, real_value)

    # Some urls are only available with POST
    if url in POST_URLS:
        response = client.post("/" + url, follow=True)
    else:
        response = client.get("/" + url, follow=True)

    assert (
        "Log in" in response.content.decode()
        or "Authentication credentials were not provided." in response.content.decode()
    )

    # Make sure the url also has MFA enabled
    url = reverse("login")
    data = {"username": new_hire.email, "password": "strong_pass"}
    response = client.post(url, data, follow=True)
    assert "/mfa/" in response.redirect_chain[-1][0]


@pytest.mark.django_db
@patch(
    "requests.post",
    Mock(return_value=Mock(status_code=200, json=lambda: {"access_token": "test"})),
)
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200, json=lambda: {"email": "hello@chiefonboarding.com"}
        )
    ),
)
def test_google_login(client, new_hire_factory, integration_factory):
    # Start with credentials enabled
    org = Organization.object.get()
    org.google_login = False
    org.save()

    new_hire1 = new_hire_factory(email="hello@chiefonboarding.com")
    new_hire_factory(email="stan@chiefonboarding.com")

    # Google login is disabled, so url doesn't work
    url = reverse("google_login")
    response = client.get(url)

    assert response.status_code == 404

    # Enable Google login
    org.google_login = True
    org.save()

    response = client.get(url)

    assert response.status_code == 200
    assert "Google login access token has not been set" in response.content.decode()

    integration_factory(integration=3)

    # Logging in with account
    response = client.get(url, follow=True)

    user = auth.get_user(client)
    # User is logged in
    assert user.is_authenticated
    assert user.email == new_hire1.email


@pytest.mark.django_db
@patch("requests.post", Mock(return_value=Mock(status_code=200, json=lambda: {})))
def test_google_login_error(client, new_hire_factory, integration_factory):
    # Start with credentials enabled
    org = Organization.object.get()
    org.google_login = True
    org.save()

    integration_factory(integration=3)
    url = reverse("google_login")

    new_hire_factory(email="hello@chiefonboarding.com")
    new_hire_factory(email="stan@chiefonboarding.com")

    response = client.get(url)

    # Try logging in with account, getting back an empty json from Google
    response = client.get(url, follow=True)

    user = auth.get_user(client)
    # User is not logged in
    assert not user.is_authenticated
    assert (
        "Something went wrong with reaching Google. Please try again."
        in response.content.decode()
    )


@pytest.mark.django_db
@patch(
    "requests.post",
    Mock(return_value=Mock(status_code=200, json=lambda: {"access_token": "test"})),
)
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200, json=lambda: {"email": "hello123@chiefonboarding.com"}
        )
    ),
)
def test_google_login_user_not_exists(client, new_hire_factory, integration_factory):
    # Start with credentials enabled
    org = Organization.object.get()
    org.google_login = True
    org.save()

    integration_factory(integration=3)
    url = reverse("google_login")

    new_hire_factory(email="hello@chiefonboarding.com")
    new_hire_factory(email="stan@chiefonboarding.com")

    response = client.get(url)

    # Try logging in with account, getting back an empty json from Google
    response = client.get(url, follow=True)

    user = auth.get_user(client)
    # User is not logged in - does not exist
    assert not user.is_authenticated
    assert (
        "There is no account associated with your email address."
        in response.content.decode()
    )


@pytest.mark.django_db
@patch(
    "requests.post",
    Mock(return_value=Mock(status_code=200, json=lambda: {"access_token": "test"})),
)
def test_oidc_login(client, new_hire_factory, settings):
    # Start with credentials enabled
    org = Organization.object.get()
    org.oidc_login = False
    org.save()

    new_hire1 = new_hire_factory(email="hello@chiefonboarding.com")
    new_hire_factory(email="stan@chiefonboarding.com")

    # OIDC login is disabled, so url doesn't work
    url = reverse("oidc_login")
    response = client.get(url)

    assert response.status_code == 200
    assert "OIDC login has not been enabled." in response.content.decode()
    # Enable OIDC login
    org.oidc_login = True
    org.save()

    response = client.get(url)

    assert response.status_code == 200
    assert "OIDC login has not been set" in response.content.decode()

    settings.OIDC_CLIENT_ID = "test"
    settings.OIDC_CLIENT_SECRET = "test"
    settings.OIDC_AUTHORIZATION_URL = "https://example.org"
    settings.OIDC_TOKEN_URL = "http://localhost:8000"
    settings.OIDC_USERINFO_URL = "http://localhost:8000"
    settings.BASE_URL = "http://localhost:8000"
    # Get the url to the OIDC server
    response = client.get(url)
    assert (
        response["location"]
        == "https://example.org?client_id=test&response_type=code&scope=openid+email+profile&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fauth%2Foidc_login%2F"
    )
    assert response.status_code == 302

    # The OIDC returns a code to authorize with, we use it to log the user in
    with patch(
        "requests.get",
        Mock(
            return_value=Mock(
                status_code=200,
                json=lambda: {
                    "sub": "test",
                    "email": "hello@chiefonboarding.com",
                    "name": "given_name family_name",
                },
            )
        ),
    ):
        response = client.get(url + "?code=test")

    user = auth.get_user(client)
    # User is logged in
    assert user.is_authenticated
    assert user.email == new_hire1.email


@pytest.mark.django_db
@patch("requests.post", Mock(return_value=Mock(status_code=200, json=lambda: {})))
@patch(
    "requests.get",
    Mock(return_value=Mock(status_code=500)),
)
def test_oidc_login_error(client, new_hire_factory, settings):
    # Start with credentials enabled
    org = Organization.object.get()
    org.oidc_login = True
    org.save()

    url = reverse("oidc_login")

    new_hire_factory(email="hello@chiefonboarding.com")
    new_hire_factory(email="stan@chiefonboarding.com")
    settings.OIDC_CLIENT_ID = "test"
    settings.OIDC_CLIENT_SECRET = "test"
    settings.OIDC_AUTHORIZATION_URL = "http://localhost"
    settings.OIDC_TOKEN_URL = "http://localhost"
    settings.OIDC_USERINFO_URL = "http://localhost"

    # Try logging in with account, getting back an empty json from OIDC
    response = client.get(url + "?code=test", follow=True)

    user = auth.get_user(client)
    # User is not logged in
    assert not user.is_authenticated
    assert (
        "Something went wrong with reaching OIDC. Please try again."
        in response.content.decode()
    )


@pytest.mark.django_db
@patch(
    "requests.post",
    Mock(return_value=Mock(status_code=200, json=lambda: {"access_token": "test"})),
)
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200, json=lambda: {"name": "given_name family_name"}
        )
    ),
)
def test_oidc_login_user_not_exists(client, settings):
    # Start with credentials enabled
    org = Organization.object.get()
    org.oidc_login = True
    org.save()

    url = reverse("oidc_login")

    settings.OIDC_CLIENT_ID = "test"
    settings.OIDC_CLIENT_SECRET = "test"
    settings.OIDC_AUTHORIZATION_URL = "http://localhost"
    settings.OIDC_TOKEN_URL = "http://localhost"
    settings.OIDC_USERINFO_URL = "http://localhost"

    # Try logging in with account, getting back an empty(no email address) json from OIDC
    response = client.get(url + "?code=test", follow=True)

    user = auth.get_user(client)
    # User is not logged in - does not exist
    assert not user.is_authenticated
    assert "Cannot get your email address." in response.content.decode()
