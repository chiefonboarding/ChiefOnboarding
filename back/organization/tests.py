import json
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from misc.models import File

from .models import Notification, Organization


@pytest.mark.django_db
def test_icon(
    introduction_factory,
    appointment_factory,
    badge_factory,
    to_do_factory,
    integration_config_factory,
    pending_admin_task_factory,
    resource_factory,
    preboarding_factory,
    admin_task_factory,
    hardware_factory,
    integration_factory,
    sequence_factory,
):
    intro = introduction_factory()
    appointment = appointment_factory()
    badge = badge_factory()
    to_do = to_do_factory()
    integration_config = integration_config_factory()
    pending_admin_task = pending_admin_task_factory()
    resource = resource_factory()
    preboarding = preboarding_factory()
    admin_task = admin_task_factory()
    hardware = hardware_factory()
    integration = integration_factory()
    sequence = sequence_factory()

    assert "icon-tabler-user" in intro.get_icon_template()
    assert "badge" in badge.get_icon_template()
    assert "calendar-event" in appointment.get_icon_template()
    assert "checkbox" in to_do.get_icon_template()
    assert "location" in integration_config.get_icon_template()
    assert "list-check" in pending_admin_task.get_icon_template()
    assert "folders" in resource.get_icon_template()
    assert "list-details" in preboarding.get_icon_template()
    assert "list-check" in admin_task.get_icon_template()
    assert "devices" in hardware.get_icon_template()
    assert "location" in integration.get_icon_template()
    assert "subtask" in sequence.get_icon_template()


@pytest.mark.django_db
def test_str(introduction_factory, appointment_factory, preboarding_factory):
    intro = introduction_factory()
    appointment = appointment_factory()
    preboarding = preboarding_factory()

    assert intro.name == str(intro)
    assert appointment.name in str(appointment)
    assert preboarding.name in str(preboarding)


@pytest.mark.django_db
def test_use_custom_email_template(new_hire_factory):
    new_hire = new_hire_factory()
    org = Organization.object.get()

    org.custom_email_template = """
    {% load general %}
     <html><body>
     This is it!
       {% for i in content %}
          {% if i.type == 'paragraph' %}
            <p style="font-size: 16px; line-height: 1.625; color: #51545E;
            margin: .4em 0 1.1875em;">
                {{i.data.text|safe|personalize:user}}
            </p>
          {% endif %}
       {% endfor %}
    </body></html>"""

    org.save()

    email = org.create_email(
        {
            "user": new_hire,
            "content": [{"type": "paragraph", "data": {"text": "hi {{first_name}}!"}}],
        }
    )

    assert "This is it!" in email
    assert f"hi {new_hire.first_name}!" in email


@pytest.mark.django_db
def test_cache_logo_url(settings, file_factory, monkeypatch):
    settings.AWS_ACCESS_KEY_ID = "xxx"
    settings.AWS_STORAGE_BUCKET_NAME = "xxx"

    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "test")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")

    file1 = file_factory()
    file2 = file_factory()
    org = Organization.object.get()

    assert org.get_logo_url == ""

    org.logo = file1
    org.save()

    # delete cache
    del org.get_logo_url

    # Duplicate it so we are not referencing it
    logo_url = "".join(org.get_logo_url)

    assert cache.get("logo_url", None) is not None
    assert cache.get("logo_url", None) == logo_url

    org.get_logo_url

    # Delete cache
    del org.get_logo_url

    assert org.get_logo_url == logo_url

    # Invalidate cache with new logo

    org.logo = file2
    org.save()

    # Delete cache
    del org.get_logo_url

    assert org.get_logo_url != logo_url


@pytest.mark.django_db
def test_file_url(settings, client, new_hire_factory, file_factory, monkeypatch):
    settings.AWS_ACCESS_KEY_ID = "xxx"
    settings.AWS_STORAGE_BUCKET_NAME = "xxx"
    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "test")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")

    new_hire = new_hire_factory()
    file1 = file_factory()
    file2 = file_factory()
    client.force_login(new_hire)

    # Invalid request
    url = reverse("organization:get_file", args=[file1.id, file2.uuid])
    response = client.get(url)

    assert response.status_code == 404

    # Valid request
    url = reverse("organization:get_file", args=[file1.id, file1.uuid])
    response = client.get(url)

    assert response.status_code == 200
    assert file1.key in response.content.decode()

    # Create new file object
    url = reverse("organization:create_file")
    response = client.post(url, {"name": "new_file.png"})

    assert File.objects.count() == 3
    newest_file = File.objects.last()

    assert newest_file.name == "new_file.png"
    assert newest_file.ext == "png"

    response = json.loads(response.content.decode())

    assert response["success"] == 1
    assert "aws" in response["file"]["url"]
    assert response["file"]["id"] == newest_file.id
    assert newest_file.key in response["file"]["get_url"]


@pytest.mark.django_db
def test_file_delete_as_new_hire(client, new_hire_factory, file_factory):
    new_hire = new_hire_factory()
    file1 = file_factory()

    client.force_login(new_hire)

    assert File.objects.all().count() == 1

    # Cannot delete file object as a new hire
    url = reverse("organization:file", args=[file1.id])
    response = client.delete(url)

    assert File.objects.all().count() == 1
    assert response.status_code == 204


@pytest.mark.django_db
def test_notification_can_delete(notification_factory):
    not1 = notification_factory(notification_type=Notification.Type.ADDED_TODO)

    assert not not1.can_delete

    # Correct notification type and date is within limit
    not1.notification_type = Notification.Type.ADDED_SEQUENCE
    not1.save()

    assert not1.can_delete

    # date is now outside of limit
    not1.created = timezone.now() - timedelta(days=3)
    not1.save()

    assert not not1.can_delete


@pytest.mark.no_run_around_tests
@pytest.mark.django_db(reset_sequences=True)
def test_initial_setup_page(client):
    # account login redirects to setup page
    url = reverse("account_login")
    response = client.get(url, follow=True)
    assert reverse("setup") == response.redirect_chain[-1][0]

    url = reverse("setup")
    response = client.get(url)

    # page renders, no org created yet
    assert response.status_code == 200
    assert "Organization" in response.content.decode()
    assert "First name" in response.content.decode()
    assert "Last name" in response.content.decode()
    assert "Language" in response.content.decode()

    assert not Organization.objects.all().exists()
    assert not get_user_model().objects.all().exists()

    response = client.post(
        url,
        data={
            "name": "test org",
            "language": "en",
            "timezone": "UTC",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john1@chiefonboarding.com",
            "password1": "superstrongpss123",
            "password2": "superstrongpss123",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Organization.objects.all().exists()
    assert get_user_model().objects.all().exists()


@pytest.mark.django_db
def test_initial_setup_page_with_org_created(client):
    url = reverse("setup")
    response = client.get(url)

    # shows 404 as org is already there
    assert response.status_code == 404


@pytest.mark.django_db
def test_reset_timed_triggers_last_check_command():
    # pretend task has not ran for a while by setting the last_check back a day
    org = Organization.objects.get()
    org.timed_triggers_last_check = timezone.now() - timedelta(days=1)
    org.save()

    # run command to set it back to now
    call_command("reset_timed_triggers_last_check")

    org.refresh_from_db()
    # avoid milisecond/second differences between call and check
    assert org.timed_triggers_last_check.replace(
        second=0, microsecond=0
    ) == timezone.now().replace(second=0, microsecond=0)


@pytest.mark.no_run_around_tests
@pytest.mark.django_db
def test_reset_timed_triggers_last_check_command_with_no_org():
    # Just testing if command runs without error when no org is present
    call_command("reset_timed_triggers_last_check")


@pytest.mark.django_db()
def test_health_check(client):
    response = client.get("/health")
    assert response.content.decode() == "ok"


@pytest.mark.django_db
def test_search(
    client,
    to_do_factory,
    resource_factory,
    badge_factory,
    appointment_factory,
    introduction_factory,
    preboarding_factory,
    integration_factory,
    sequence_factory,
    hardware_factory,
    employee_factory,
    admin_factory,
):
    admin = admin_factory()
    client.force_login(admin)

    to_do = to_do_factory(name="test to_do")
    resource = resource_factory(name="test resource")
    badge = badge_factory(name="test badge")
    appointment = appointment_factory(name="test appointment")
    introduction = introduction_factory(name="test introduction")
    preboarding = preboarding_factory(name="test preboarding")
    integration = integration_factory(name="test integration")
    sequence = sequence_factory(name="test sequence")
    hardware = hardware_factory(name="test hardware")
    employee1 = employee_factory(first_name="john", last_name="test")
    employee2 = employee_factory(first_name="john", last_name="do")

    url = reverse("organization:search")
    response = client.get(url + "?q=test")

    assert to_do.name in response.content.decode()
    assert resource.name in response.content.decode()
    assert badge.name in response.content.decode()
    assert appointment.name in response.content.decode()
    assert introduction.name in response.content.decode()
    assert preboarding.name in response.content.decode()
    assert integration.name in response.content.decode()
    assert sequence.name in response.content.decode()
    assert hardware.name in response.content.decode()
    assert employee1.full_name in response.content.decode()
    # doesn't have the "test" query in it
    assert employee2.full_name not in response.content.decode()
