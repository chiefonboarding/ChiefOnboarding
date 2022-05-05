import pytest


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
