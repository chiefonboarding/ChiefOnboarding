import pytest
from django.urls import reverse

from admin.integrations.models import Integration


@pytest.mark.django_db
def test_create_integration(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("integrations:create")
    response = client.get(url)

    assert "Add new integration" in response.content.decode()

    # Post with invalid JSON
    response = client.post(url, {"name": "test", "manifest": '{"test": "Test",}'})

    assert "Enter a valid JSON." in response.content.decode()

    # Post with valid JSON
    response = client.post(url, {"name": "test", "manifest": '{"test": "Test"}'})

    assert "Enter a valid JSON." not in response.content.decode()
    assert Integration.objects.filter(integration=10).count() == 1


@pytest.mark.django_db
def test_update_integration(client, django_user_model, custom_integration_factory):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    url = reverse("integrations:update", args=[integration.id])
    response = client.get(url)

    assert "Add new integration" in response.content.decode()
    assert "TEAM_ID" in response.content.decode()
    assert integration.name in response.content.decode()


@pytest.mark.django_db
def test_delete_integration(client, django_user_model, custom_integration_factory):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    assert Integration.objects.filter(integration=10).count() == 1

    url = reverse("integrations:delete", args=[integration.id])
    response = client.get(url, follow=True)

    assert "Are you sure you want to remove this integration?" in response.content.decode()

    response = client.delete(url, follow=True)

    assert reverse("settings:integrations") in response.redirect_chain[-1][0]
    assert Integration.objects.filter(integration=10).count() == 0


@pytest.mark.django_db
def test_integration_extra_args_form(client, django_user_model, custom_integration_factory):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    url = reverse("integrations:update-creds", args=[integration.id])
    response = client.get(url)

    assert "Please put your token here" in response.content.decode()
    assert "Organization id" in response.content.decode()
    assert 'name="ORG"' in response.content.decode()
    assert 'name="TOKEN"' in response.content.decode()

    response = client.post(url, {"ORG": "123", "TOKEN": "SECRET_TOKEN", "NOTWORKING": "False"}, follow=True)

    integration = Integration.objects.first()
    assert integration.extra_args == {"ORG": "123", "TOKEN": "SECRET_TOKEN"}

