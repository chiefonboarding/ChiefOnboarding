
import pytest
from allauth.mfa.models import Authenticator
from django.contrib import auth
from django.urls import reverse

from .test_utils import get_all_urls

# No need to login for those urls
# These are public pages or authentication happens in a different way
WHITELISTED_URLS = [
    "robots.txt",
    "logout/",
    "password/reset/",
    "password/reset/done/",
    "^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
    "password/reset/key/done/",
    "api/slack/bot",
    "new_hire/preboarding/",
    "new_hire/slackform/<int:pk>/",
    "setup/",
    "login/",
    "social/login/cancelled/",
    "social/login/error/",
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

    url = reverse("account_login")
    data = {"login": email, "password": password}
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

    url = reverse("account_login")
    data = {"login": new_hire.email, "password": "strong_pass"}
    response = client.post(url, data=data, follow=True)
    user = auth.get_user(client)
    assert user.is_authenticated
    assert redirect_url == response.redirect_chain[-1][0]


# @pytest.mark.django_db
# def test_credentials_setting(client, new_hire_factory):
#     # Start with credentials enabled
#     new_hire_factory(email="user@example.com")
#     org = Organization.object.get()
#     org.credentials_login = True
#     org.save()
#     response = client.get(reverse("account_login"))

#     # Login form should be here
#     assert "id_login" in response.content.decode()
#     assert "id_password" in response.content.decode()
#     assert "Log in" in response.content.decode()

#     # Disable credentials login
#     org.credentials_login = False
#     org.save()

#     # Login form should be gone
#     response = client.get(reverse("account_login"))
#     assert "id_login" not in response.content.decode()
#     assert "id_password" not in response.content.decode()
#     assert "Log in" not in response.content.decode()

#     # Posting to login form will result in 404
#     response = client.post(
#         reverse("account_login"), data={"login": "test", "password": "test"}
#     )
#     assert "Not Found" in response.content.decode()


# @pytest.mark.django_db
# def test_google_login_setting(client, new_hire_factory, integration_factory):
#     # Start with credentials enabled
#     new_hire_factory(email="user@example.com")
#     integration_factory(integration=Integration.Type.GOOGLE_LOGIN)

#     org = Organization.object.get()
#     org.google_login = True
#     org.save()
#     response = client.get(reverse("account_login"))

#     # Login form should be here
#     assert "Log in with Google" in response.content.decode()

#     # Disable credentials login
#     org.google_login = False
#     org.save()

#     # Login form should be gone
#     response = client.get(reverse("account_login"))
#     assert "Log in with Google" not in response.content.decode()


# @pytest.mark.django_db
# def test_oidc_login_setting(client, new_hire_factory, settings):
#     # Start with credentials enabled
#     new_hire_factory(email="user@example.com")

#     org = Organization.object.get()
#     org.oidc_login = True
#     org.save()
#     response = client.get(reverse("account_login"))
#     # make sure the login form is there
#     settings.OIDC_FORCE_AUTHN = False
#     # Login form should be here
#     login_name = "Log in with " + settings.OIDC_LOGIN_DISPLAY
#     assert login_name in response.content.decode()

#     # Disable credentials login
#     org.oidc_login = False
#     org.save()

#     # Login form should be gone
#     response = client.get(reverse("account_login"))
#     assert login_name not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("url", get_all_urls())
def test_authed_view(url, client, new_hire_factory):
    # This test is only here to check that we aren't accidentally exposing any urls to
    # the public (without authentication)
    new_hire = new_hire_factory()
    # also add mfa
    Authenticator.objects.create(user=new_hire, type=Authenticator.Type.TOTP, data={})
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
    url = reverse("account_login")
    data = {"login": new_hire.email, "password": "strong_pass"}
    response = client.post(url, data, follow=True)
    assert "/authenticate/" in response.redirect_chain[-1][0]
