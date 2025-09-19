import pytest
from django.contrib import auth
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email, password, logged_in",
    [
        ("", "", False),
        ("", "strong_pass", False),
        ("user@example.com", "", False),
        ("user@example.com", "invalid_pass", False),
        ("user@example.com", "strong_pass", True),
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


@pytest.mark.django_db
@override_settings(SOCIALACCOUNT_ONLY=True)
def test_disabled_credentials_login(client):
    response = client.get(reverse("account_login"))
    assert "Forgot your password?" not in response.content.decode()

    response = client.post(
        reverse("account_login"), data={"login": "test@test.com", "password": "test"}
    )
    assert response.status_code == 403
