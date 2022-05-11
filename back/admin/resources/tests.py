import pytest
from django.urls import reverse

from admin.resources.factories import *  # noqa
from admin.resources.models import Chapter, Resource


@pytest.mark.django_db
def test_create_resource(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("resources:create")
    response = client.get(url)

    assert "Create resource item" in response.content.decode()

    data = {
        "name": "Resource item 1",
        "tags": ["hi", "whoop"],
        "on_day": 1,
        "chapters": '[{ "id": "tesk243", "name": "Continuing Education", "content": { "time": 0, "blocks": [{ "data": { "text": "One of our core values is “Be better today" }, "type": "paragraph" }]}, "type": 0, "children": [], "order": 0 }]',  # noqa: E501
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Resource.objects.all().count() == 1


@pytest.mark.django_db
def test_create_resource_with_inner_chapters(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("resources:create")
    response = client.get(url)

    assert "Create resource item" in response.content.decode()

    data = {
        "name": "Resource item 1",
        "tags": ["hi", "whoop"],
        "on_day": 1,
        "chapters": '[{ "id": "tesk243", "name": "Continuing Education", "content": { "time": 0, "blocks": [{ "data": { "text": "One of our core values is “Be better today" }, "type": "paragraph" }]}, "type": 0, "children": [{ "id": "23434", "name": "Inner test", "content": { "time": 0, "blocks": [{ "data": { "text": "This is an inner one" }, "type": "paragraph" }]}, "type": 0, "children": [], "order": 1 }], "order": 0 }]',  # noqa: E501
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Resource.objects.all().count() == 1
    assert Chapter.objects.all().count() == 2

    top_chapter = Chapter.objects.get(name="Continuing Education")
    inner_chapter = Chapter.objects.get(name="Inner test")

    assert not top_chapter.parent_chapter
    assert inner_chapter.parent_chapter

@pytest.mark.django_db
def test_update_resource(client, django_user_model, resource_factory):
    client.force_login(django_user_model.objects.create(role=1))
    resource = resource_factory()
    url = resource.update_url
    response = client.get(url)

    assert "Update resource item" in response.content.decode()
    assert resource.name in response.content.decode()
    assert Chapter.objects.all().count() == 2

    first_chapter_id = resource.chapters.all().first().id
    second_chapter_id = resource.chapters.all()[1].id

    data = {
        "name": "Resource item 2",
        "tags": ["hi", "whoop"],
        "chapters": '[{ "id": '
        + str(first_chapter_id)
        + ', "name": "new chapter", "content": { "time": 0, "blocks": [] }, "type": 0, "children": [] }, { "id": '  # noqa: E501
        + str(second_chapter_id)
        + ', "name": "Some Questions", "content": { "time": 0, "blocks": [] }, "type": 2, "children": [] }]',  # noqa: E501
        "on_day": 1,
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert reverse("resources:list") == response.redirect_chain[-1][0]

    assert Resource.objects.all().count() == 1
    # Check that it didn't duplicate chapters, but reused them
    assert Chapter.objects.all().count() == 2


@pytest.mark.django_db
def test_chapter_slack_title(chapter_factory):
    chapter = chapter_factory(name="Test chapter")
    parent_chapter = chapter_factory(name="parent chapter")
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
                "te..."
            ),
            "emoji": True,
        },
        "value": str(chapter.id),
    }
    assert chapter.slack_menu_item() == expected_menu_item

    # Check with parent chapter
    chapter.parent_chapter = parent_chapter
    chapter.save()

    expected_menu_item = {
        "text": {
            "type": "plain_text",
            "text": (
                "- Hello, this is a new title, just trying to hit 75 chars here. Test "
                "te..."
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
def test_next_chapter_not_course(
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "current_chapter, new_chapter_title",
    [
        ("inner_lvl3_1", "inner_lvl3_2"),
        ("inner_lvl3_2", "top_lvl4_q"),
        ("top_lvl4_q", None),
    ],
)
def test_next_chapter_is_course(
    current_chapter, new_chapter_title, resource_with_level_deep_chapters_factory
):
    resource = resource_with_level_deep_chapters_factory()

    current_chapter = Chapter.objects.get(name=current_chapter).id
    # Check if it returned None when it's on the last item
    if new_chapter_title is None:
        assert resource.next_chapter(current_chapter, True) is None
        return

    assert resource.next_chapter(current_chapter, True) == Chapter.objects.get(
        name=new_chapter_title
    )


@pytest.mark.django_db
def test_duplicate_chapter(resource_with_level_deep_chapters_factory):
    orig = resource_with_level_deep_chapters_factory()
    orig_id = orig.id
    dupe = orig.duplicate()

    amount_chapters = dupe.chapters.all().count()

    # Fetch resource again as id changed
    original_resource = Resource.objects.get(id=orig_id)

    # Check that all chapter ids are different
    for chapter in dupe.chapters.all():
        original_chapter = original_resource.chapters.get(name=chapter.name)
        assert original_chapter.id != chapter.id

    # Delete first resource
    original_resource.delete()

    dupe.refresh_from_db()

    # Amount of chapters should also be half now
    total_amount_chapters = Chapter.objects.all().count()

    assert dupe.chapters.count() == total_amount_chapters
    assert dupe.chapters.count() == amount_chapters


@pytest.mark.django_db
def test_search_resources(
    django_user_model, resource_with_level_deep_chapters_factory, resource_factory
):
    user = django_user_model.objects.create(role=1)

    # Will find the item in the first one
    resource1 = resource_with_level_deep_chapters_factory()

    # Won't find it in this one
    resource_factory()

    # Search for it
    resources = Resource.objects.search(user, "inner_")

    # Won't find it as it's not assigned to the user
    assert resources.count() == 0

    # Add resource to user
    user.resources.add(resource1)

    # Search for it
    resources = Resource.objects.search(user, "inner_")
    assert resources.count() == 1
    assert resources.first() == resource1
