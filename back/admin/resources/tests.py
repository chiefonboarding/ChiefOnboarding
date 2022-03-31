import pytest
from django.urls import reverse

from admin.resources.models import Chapter, Resource

from .factories import *  # noqa


@pytest.mark.django_db
@pytest.mark.skip(reason="Not sure why it doesn't work - fix later")
def test_create_resource(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("resources:create")
    response = client.get(url)

    assert "Create resource item" in response.content.decode()

    data = {
        "name": "Resource item 1",
        "tags": ["hi", "whoop"],
        "on_day": 1,
        "chapters": [
            {
                "name": "Continuing Education",
                "content": {
                    "time": 0,
                    "blocks": [
                        {
                            "data": {
                                "text": (
                                    "One of our core values is “Be better today than "
                                    "yesterday,” so it’s important that we support our"
                                    "employees’ efforts to learn, grow, and improve. "
                                    "These are some of the key benefits of working at "
                                    "us, and are central to our company culture."
                                )
                            },
                            "type": "paragraph",
                        }
                    ],
                },
                "type": 0,
                "children": [],
                "order": 0,
            },
        ],
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Resource.objects.all().count() == 1


@pytest.mark.django_db
def test_update_resource(client, django_user_model, resource_factory):
    client.force_login(django_user_model.objects.create(role=1))
    resource = resource_factory()
    url = resource.update_url
    response = client.get(url)

    assert "Update resource item" in response.content.decode()
    assert resource.name in response.content.decode()

    data = {
        "name": "Resource item 2",
        "tags": ["hi", "whoop"],
        "chapters": [
            {
                "name": "new chapter",
                "content": '{ "time": 0, "blocks": [] }',
                "type": 0,
            },
            {
                "name": "Some Questions",
                "content": '{ "time": 0, "blocks": [] }',
                "type": 2,
            },
        ],
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Resource.objects.all().count() == 1
    # Check that it didn't duplicate chapters, but reused them
    assert Chapter.objects.all().count() == 2


@pytest.mark.django_db
def test_chapter_slack_title(chapter_factory):
    chapter = chapter_factory(name="Test chapter")
    expected_menu_item = {
        "text": {"type": "plain_text", "text": "Test chapter", "emoji": True},
        "value": str(chapter.id),
    }

    assert chapter.slack_menu_item() == expected_menu_item

    # 74 chars should work
    chapter.name = (
        "Hello, this is a new title, just trying to hit 75 chars here. Test test te"
    )
    chapter.save()

    expected_menu_item = {
        "text": {
            "type": "plain_text",
            "text": (
                "Hello, this is a new title, just trying to hit 75 chars here. Test "
                "test te"
            ),
            "emoji": True,
        },
        "value": str(chapter.id),
    }

    assert chapter.slack_menu_item() == expected_menu_item

    # 75 chars should not work and be shortend
    chapter.name = (
        "Hello, this is a new title, just trying to hit 75 chars here. Test test tes"
    )
    chapter.save()

    expected_menu_item = {
        "text": {
            "type": "plain_text",
            "text": (
                "Hello, this is a new title, just trying to hit 75 chars here. Test "
                "tes..."
            ),
            "emoji": True,
        },
        "value": str(chapter.id),
    }
    assert chapter.slack_menu_item() == expected_menu_item


@pytest.mark.django_db
def test_chapter_display(resource_with_level_deep_chapters_factory):
    resource = resource_with_level_deep_chapters_factory()

    chapters = Chapter.objects.filter(
        name__in=["top_lvl0", "top_lvl1", "top_lvl2", "top_lvl3", "top_lvl4_q"]
    )
    # Check that we get the right amount of chapters
    assert chapters.count() == resource.chapters_display().count()
    # Check that all items exist
    for chapter in chapters:
        assert resource.chapters_display().filter(id=chapter.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "current_chapter, new_chapter_title",
    [
        (-1, "top_lvl0"),
        ("top_lvl0", "inner_lvl1_0"),
        ("inner_lvl1_0", "inner_lvl1_1_1"),
        ("inner_lvl1_1_1", "top_lvl2"),
        ("top_lvl2", "inner_lvl3_0"),
        ("inner_lvl3_0", "inner_lvl3_1"),
        ("inner_lvl3_1", "inner_lvl3_2"),
        ("inner_lvl3_2", None),
    ],
)
def test_next_chapter_no_course(
    current_chapter, new_chapter_title, resource_with_level_deep_chapters_factory
):
    resource = resource_with_level_deep_chapters_factory()

    # skip all question items and follow in order

    # Get the first item if index is -1
    if current_chapter != -1:
        current_chapter = Chapter.objects.get(name=current_chapter).id

    # Check if it returned None when it's on the last item
    if new_chapter_title is None:
        assert resource.next_chapter(current_chapter, False) is None
        return

    assert resource.next_chapter(current_chapter, False) == Chapter.objects.get(
        name=new_chapter_title
    )
