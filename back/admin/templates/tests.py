import pytest
from django.apps import apps
from django.urls import reverse

from admin.introductions.factories import IntroductionFactory  # noqa
from admin.to_do.factories import ToDoFactory  # noqa
from admin.badges.factories import BadgeFactory  # noqa


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, app, model",
    [
        ("todo:list", "to_do", "todo"),
        ("introductions:list", "introductions", "introduction"),
        ("badges:list", "badges", "badge"),
    ],
)
def test_templates_crud(
    client,
    django_user_model,
    url,
    app,
    model,
):
    # Force admin to login
    client.force_login(django_user_model.objects.create(role=1))

    # Get list view of template
    url = reverse(url)
    response = client.get(url)

    # There aren't any objects yet
    assert "No items available" in response.content.decode()

    # Create template object for every template and 2 non-template
    ToDoFactory()
    ToDoFactory(template=False)
    ToDoFactory(template=False)

    IntroductionFactory()
    IntroductionFactory(template=False)
    IntroductionFactory(template=False)

    BadgeFactory()
    BadgeFactory(template=False)
    BadgeFactory(template=False)

    # Get first object of template
    object_model = apps.get_model(app, model)
    obj = object_model.objects.first()

    # Check list page again
    response = client.get(url)

    # Should be one object
    assert "No items available" not in response.content.decode()
    assert obj.name in response.content.decode()

    # Go to object
    response = client.get(obj.update_url)
    assert response.status_code == 200
    assert obj.name in response.content.decode()

    url = reverse("templates:duplicate", args=[model, obj.id])
    response = client.post(url)

    assert object_model.objects.all().count() == 4
    assert object_model.templates.all().count() == 2

    # Delete first object
    response = client.post(obj.delete_url, follow=True)
    assert response.status_code == 200
    # Second object is still here
    assert "(duplicate)" in response.content.decode()
    assert object_model.templates.all().count() == 1
    assert "item has been removed" in response.content.decode()
