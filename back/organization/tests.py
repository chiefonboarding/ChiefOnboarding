import json

import pytest
from django.core.cache import cache
from django.urls import reverse

from misc.models import File

from .models import Organization


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

    assert "icon-tabler-user" in intro.get_icon_template
    assert "badge" in badge.get_icon_template
    assert "calendar-event" in appointment.get_icon_template
    assert "checkbox" in to_do.get_icon_template
    assert "location" in integration_config.get_icon_template
    assert "list-check" in pending_admin_task.get_icon_template
    assert "folders" in resource.get_icon_template
    assert "list-details" in preboarding.get_icon_template
    assert "list-check" in admin_task.get_icon_template


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
def test_cache_logo_url(file_factory):
    file1 = file_factory()
    file2 = file_factory()
    org = Organization.object.get()

    assert org.get_logo_url() == ""

    org.logo = file1
    org.save()

    # Duplicate it so we are not referencing it
    logo_url = "".join(org.get_logo_url())

    assert cache.get("logo_url", None) is not None
    assert cache.get("logo_url", None) == logo_url

    org.get_logo_url()

    assert org.get_logo_url() == logo_url

    # Invalidate cache with new logo

    org.logo = file2
    org.save()

    assert org.get_logo_url() != logo_url


@pytest.mark.django_db
def test_file_url(client, new_hire_factory, file_factory):
    new_hire = new_hire_factory()
    file1 = file_factory()
    file2 = file_factory()
    client.force_login(new_hire)

    # Invalid request
    url = reverse("organization:get_file", args=[file1.id, file2.uuid])
    response = client.get(url)

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
