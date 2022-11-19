import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.formats import localize
from freezegun import freeze_time

from organization.models import Organization, WelcomeMessage
from slack_bot.tasks import (
    first_day_reminder,
    introduce_new_people,
    link_slack_users,
    update_new_hire,
    birthday_reminder,
)
from slack_bot.models import SlackChannel
from slack_bot.views import (
    slack_add_sequences_to_new_hire,
    slack_catch_all_message_search_resources,
    slack_change_resource_page,
    slack_complete_admin_task,
    slack_complete_to_do,
    slack_create_new_hire_or_ask_perm,
    slack_deny_new_hire,
    slack_next_page_resource,
    slack_open_modal_for_selecting_seq_item,
    slack_open_resource_dialog,
    slack_open_todo_dialog,
    slack_save_welcome_message,
    slack_show_all_resources_categories,
    slack_show_help,
    slack_show_resources_items_in_category,
    slack_show_to_do_items,
    slack_show_to_do_items_based_on_message,
    slack_show_welcome_dialog,
)
from users.factories import ResourceUserFactory


@pytest.mark.django_db
def test_show_help(new_hire_factory):
    new_hire_factory(slack_user_id="slackx")

    slack_show_help(message={"user": "slackx"})

    assert cache.get("slack_channel") == "slackx"
    assert "Happy to help!" in cache.get("slack_text")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "func",
    [
        (slack_show_to_do_items_based_on_message),
        (slack_show_all_resources_categories),
        (slack_catch_all_message_search_resources),
    ],
)
def test_unauthed_calls(func):
    func({"user": "slackx"})

    assert cache.get("slack_channel") == "slackx"
    assert "You don't seem to be setup yet." in cache.get("slack_text")


@pytest.mark.django_db
def test_show_categories_with_no_resources(new_hire_factory):
    new_hire_factory(slack_user_id="slackx")

    slack_show_all_resources_categories({"user": "slackx"})

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "No resources available"},
        }
    ]


@pytest.mark.django_db
def test_show_categories(new_hire_factory, resource_factory):
    new_hire = new_hire_factory(slack_user_id="slackx")

    resource_without_category = resource_factory(category=None)
    resource_with_category = resource_factory()

    new_hire.resources.set([resource_without_category, resource_with_category])

    slack_show_all_resources_categories({"user": "slackx"})

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {"type": "section", "text": {"type": "mrkdwn", "text": "Select a category:"}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "No category"},
                    "style": "primary",
                    "value": "-1",
                    "action_id": "category:-1",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": resource_with_category.category.name,
                    },
                    "style": "primary",
                    "value": str(resource_with_category.category.id),
                    "action_id": f"category:{resource_with_category.category.id}",
                },
            ],
        },
    ]


@pytest.mark.django_db
def test_show_open_modal_for_selecting_seq_items():
    slack_open_modal_for_selecting_seq_item(
        {"container": {"message_ts": ""}, "trigger_id": "Test"}, {"value": "test"}
    )


@pytest.mark.django_db
def test_slack_show_resources_items_in_category_no_category(
    new_hire_factory, resource_user_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")

    resource_user1 = resource_user_factory(
        resource__category=None, user=new_hire, resource__name="1test"
    )
    resource_user2 = resource_user_factory(
        resource__category=None, user=new_hire, resource__name="2test"
    )

    ResourceUserFactory(user=new_hire)

    slack_show_resources_items_in_category({"value": "-1"}, {"user": {"id": "slackx"}})

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Here are your options:"},
        },
        {
            "type": "section",
            "block_id": str(resource_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": "*" + resource_user1.resource.name + "*",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user1.id),
                "action_id": f"dialog:resource:{resource_user1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(resource_user2.id),
            "text": {"type": "mrkdwn", "text": f"*{resource_user2.resource.name}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user2.id),
                "action_id": f"dialog:resource:{resource_user2.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_slack_show_resources_items_in_category(
    new_hire_factory, resource_user_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")

    resource_user_factory(resource__category=None, user=new_hire)
    resource_user2 = resource_user_factory(user=new_hire)

    slack_show_resources_items_in_category(
        {"value": str(resource_user2.resource.category.id)}, {"user": {"id": "slackx"}}
    )

    assert cache.get("slack_channel") == "slackx"

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Here are your options:"},
        },
        {
            "type": "section",
            "block_id": str(resource_user2.id),
            "text": {"type": "mrkdwn", "text": f"*{resource_user2.resource.name}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user2.id),
                "action_id": f"dialog:resource:{resource_user2.id}",
            },
        },
    ]


@pytest.mark.django_db
@freeze_time("2022-05-13")
def test_slack_show_to_do_items_based_on_message(new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(
        slack_user_id="slackx", start_day=datetime.now().today() - timedelta(days=2)
    )

    to_do_due_in_past1 = to_do_user_factory(to_do__due_on_day=1, user=new_hire)
    to_do_due_in_past2 = to_do_user_factory(to_do__due_on_day=1, user=new_hire)
    to_do_due_today1 = to_do_user_factory(to_do__due_on_day=3, user=new_hire)
    to_do_due_today2 = to_do_user_factory(to_do__due_on_day=3, user=new_hire)

    to_do_due_future1 = to_do_user_factory(to_do__due_on_day=10, user=new_hire)
    to_do_due_future2 = to_do_user_factory(to_do__due_on_day=5, user=new_hire)

    # test without extra text
    slack_show_to_do_items_based_on_message(
        {"user": "slackx", "text": "Show me to do items"}
    )

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past1.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past1.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past2.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past2.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past2.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today1.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today1.id),
                "action_id": f"dialog:to_do:{to_do_due_today1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today2.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today2.id),
                "action_id": f"dialog:to_do:{to_do_due_today2.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_future1.id),
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{to_do_due_future1.to_do.name}*\n"
                    "This task needs to be completed in 7 working days"
                ),
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_future1.id),
                "action_id": f"dialog:to_do:{to_do_due_future1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_future2.id),
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{to_do_due_future2.to_do.name}*\n"
                    "This task needs to be completed in 2 working days"
                ),
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_future2.id),
                "action_id": f"dialog:to_do:{to_do_due_future2.id}",
            },
        },
    ]

    slack_show_to_do_items_based_on_message(
        {"user": "slackx", "text": "Show me to do items of today"}
    )

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today1.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today1.id),
                "action_id": f"dialog:to_do:{to_do_due_today1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today2.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today2.id),
                "action_id": f"dialog:to_do:{to_do_due_today2.id}",
            },
        },
    ]

    slack_show_to_do_items_based_on_message(
        {"user": "slackx", "text": "Show me to do items that are overdue"}
    )

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past1.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past1.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past2.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past2.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past2.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_slack_catch_all_message_search_resources(
    new_hire_factory, resource_user_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")

    resource_user1 = resource_user_factory(resource__name="test", user=new_hire)
    slack_catch_all_message_search_resources({"user": "slackx", "text": "not found"})

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Unfortunately, I couldn't find anything.",
            },
        }
    ]

    slack_catch_all_message_search_resources({"user": "slackx", "text": "test"})

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Here is what I found: "},
        },
        {
            "type": "section",
            "block_id": str(resource_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": "*" + resource_user1.resource.name + "*",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user1.id),
                "action_id": f"dialog:resource:{resource_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_slack_open_todo_dialog(new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(slack_user_id="slackx")

    to_do_user1 = to_do_user_factory(user=new_hire)

    slack_open_todo_dialog(
        {"action_id": f"dialog:to_do:{to_do_user1.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 0,
            "container": {"message_ts": 0},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": 1, "text": {"text": "Here are the todo items:"}},
                    {"block_id": to_do_user1.id},
                ],
            },
        },
    )

    assert cache.get("slack_trigger_id") == 0
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "complete:to_do",
        "title": {"type": "plain_text", "text": to_do_user1.to_do.name},
        "submit": {"type": "plain_text", "text": "done"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": to_do_user1.to_do.content["blocks"][0]["data"]["text"],
                },
            }
        ],
        "private_metadata": json.dumps(
            {
                "to_do_ids_from_original_message": [to_do_user1.id],
                "text": "Here are the todo items:",
                "to_do_id": to_do_user1.id,
                "message_ts": 0,
            }
        ),
    }


@pytest.mark.django_db
def test_slack_to_do_complete_external_form(new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(slack_user_id="slackx", slack_channel_id="slackx")

    # to do item with upload field
    to_do_user1 = to_do_user_factory(
        user=new_hire,
        to_do__content={
            "time": 0,
            "blocks": [
                {
                    "data": {"text": "Please complete this item!", "type": "upload"},
                    "type": "form",
                }
            ],
        },
    )

    slack_open_todo_dialog(
        {"action_id": f"dialog:to_do:{to_do_user1.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 21212,
            "container": {"message_ts": 23123},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": "1", "text": {"text": "Here are the todo items:"}},
                    {"block_id": str(to_do_user1.id)},
                ],
            },
        },
    )

    # Form is not filled yet
    assert cache.get("slack_channel") == "slackx"
    assert (
        cache.get("slack_text")
        == "Please complete the form first. Click on 'View details' to complete it."
    )

    # Mock form filling
    to_do_user1.form = {"test": "test"}
    to_do_user1.completed = True
    to_do_user1.save()

    # Reclick the button
    slack_open_todo_dialog(
        {"action_id": f"dialog:to_do:{to_do_user1.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 21212,
            "container": {"message_ts": 23123},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": "1", "text": {"text": "Here are the todo items:"}},
                    {"block_id": str(to_do_user1.id)},
                ],
            },
        },
    )

    # Should update message now (and remove to do item)
    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "I couldn't find any tasks."},
        }
    ]


@pytest.mark.django_db
def test_open_resource_dialog(new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory(slack_user_id="slackx")

    # Should not reset steps back to one, if it's not a course
    # Resource has questions and a page. Questions should be ignored. So not showing
    # menu.
    resource_user1 = resource_user_factory(user=new_hire, step=5)

    payload = {
        "action_id": f"dialog:resource:{resource_user1.id}",
        "block_id": str(resource_user1.id),
        "text": {"type": "plain_text", "text": "View resource", "emoji": True},
        "value": str(resource_user1.id),
        "style": "primary",
        "type": "button",
        "action_ts": "1653056766.929696",
    }

    body = {
        "type": "block_actions",
        "user": {"id": "slackx", "username": "hello", "name": "hello", "team_id": "xx"},
        "api_app_id": "xxx",
        "token": "xxx",
        "container": {
            "type": "message",
            "message_ts": "1653056755.376889",
            "channel_id": "xxx",
            "is_ephemeral": False,
        },
        "trigger_id": "37055ba4a888a9526a37",
        "team": {"id": "xxx", "domain": "chiefonboarding"},
        "enterprise": None,
        "is_enterprise_install": False,
        "channel": {"id": "xxx", "name": "directmessage"},
        "message": {
            "bot_id": "xx",
            "type": "message",
            "text": "Here are your options:",
            "user": "slackx",
            "ts": "1653056755.376889",
            "app_id": "xx",
            "team": "xxx",
            "blocks": [
                {
                    "type": "section",
                    "block_id": "ZcGZ",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Here are your options:",
                        "verbatim": False,
                    },
                },
                {
                    "type": "section",
                    "block_id": str(resource_user1.id),
                    "text": {
                        "type": "mrkdwn",
                        "text": "*New course*",
                        "verbatim": False,
                    },
                    "accessory": {
                        "type": "button",
                        "action_id": f"dialog:resource:{resource_user1.id}",
                        "style": "primary",
                        "text": {
                            "type": "plain_text",
                            "text": "View resource",
                            "emoji": True,
                        },
                        "value": str(resource_user1.id),
                    },
                },
            ],
        },
        "state": {"values": {}},
        "response_url": "",
        "actions": [
            {
                "action_id": f"dialog:resource:{resource_user1.id}",
                "block_id": str(resource_user1.id),
                "text": {"type": "plain_text", "text": "View resource", "emoji": True},
                "value": str(resource_user1.id),
                "style": "primary",
                "type": "button",
                "action_ts": "1653056766.929696",
            }
        ],
    }

    slack_open_resource_dialog(payload, body)

    # Trigger id should be the same as in the body
    assert cache.get("slack_trigger_id") == "37055ba4a888a9526a37"
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "dialog:resource",
        "title": {"type": "plain_text", "text": "Resource"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{resource_user1.resource.chapters.all()[0].name}*",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Please complete this item!"},
            },
        ],
        "private_metadata": '{"current_chapter": '
        + str(resource_user1.resource.chapters.all()[0].id)
        + ', "resource_user": '
        + str(resource_user1.id)
        + "}",
    }

    resource_user1.refresh_from_db()

    assert resource_user1.step == 5


@pytest.mark.django_db
def test_change_resource_page(new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory(slack_user_id="slackx")

    resource_user1 = resource_user_factory(user=new_hire, step=5)
    # Make second chapter another page, so it shows up as a menu item
    last_chapter = resource_user1.resource.chapters.last()
    last_chapter.type = 0
    last_chapter.content = {
        "time": 0,
        "blocks": [{"data": {"text": "This is the second page"}, "type": "paragraph"}],
    }

    last_chapter.save()

    payload = {
        "type": "static_select",
        "action_id": "change_resource_page",
        "block_id": "change_resource_page",
        "selected_option": {
            "text": {"type": "plain_text", "text": "New item", "emoji": True},
            "value": str(last_chapter.id),
        },
        "placeholder": {"type": "plain_text", "text": "Select chapter", "emoji": True},
        "action_ts": "1653061762.164536",
    }

    body = {
        "type": "block_actions",
        "user": {"id": "slackx", "username": "hello", "name": "hello", "team_id": "xx"},
        "api_app_id": "xxx",
        "token": "xxx",
        "container": {"type": "view", "view_id": "view_idxxx"},
        "trigger_id": "63fe91dd9e6c568a47c804",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "enterprise": None,
        "is_enterprise_install": False,
        "view": {
            "id": "xx",
            "team_id": "xxx",
            "type": "modal",
            "blocks": [
                {
                    "type": "actions",
                    "block_id": "change_resource_page",
                    "elements": [
                        {
                            "type": "static_select",
                            "action_id": "change_resource_page",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select chapter",
                                "emoji": True,
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": resource_user1.resource.chapters.first().name,  # noqa
                                        "emoji": True,
                                    },
                                    "value": str(
                                        resource_user1.resource.chapters.first().id
                                    ),
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": resource_user1.resource.chapters.last().name,  # noqa
                                        "emoji": True,
                                    },
                                    "value": str(
                                        resource_user1.resource.chapters.last().id
                                    ),
                                },
                            ],
                        }
                    ],
                },
                {
                    "type": "section",
                    "block_id": "g5h0",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{resource_user1.resource.chapters.first().name}*",
                        "verbatim": False,
                    },
                },
            ],
            "private_metadata": '{"current_chapter": '
            + str(resource_user1.resource.chapters.first().id)
            + ', "resource_user": '
            + str(resource_user1.id)
            + "}",
            "callback_id": "dialog:resource",
            "state": {
                "values": {
                    "change_resource_page": {
                        "change_resource_page": {
                            "type": "static_select",
                            "selected_option": {
                                "text": {
                                    "type": "plain_text",
                                    "text": resource_user1.resource.chapters.last().name,  # noqa
                                    "emoji": True,
                                },
                                "value": str(
                                    resource_user1.resource.chapters.last().id
                                ),
                            },
                        }
                    }
                }
            },
            "hash": "klsdf.lksdf",
            "title": {"type": "plain_text", "text": "Resource", "emoji": True},
            "clear_on_close": False,
            "notify_on_close": False,
            "close": None,
            "submit": {"type": "plain_text", "text": "Next", "emoji": True},
            "previous_view_id": None,
            "root_view_id": "lksdkdkd",
            "app_id": "xxx",
            "external_id": "",
            "app_installed_team_id": "xxx",
            "bot_id": "B03CWBH49NW",
        },
        "actions": [
            {
                "type": "static_select",
                "action_id": "change_resource_page",
                "block_id": "change_resource_page",
                "selected_option": {
                    "text": {
                        "type": "plain_text",
                        "text": resource_user1.resource.chapters.last().name,
                        "emoji": True,
                    },
                    "value": str(resource_user1.resource.chapters.last().id),
                },
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select chapter",
                    "emoji": True,
                },
                "action_ts": "1653079877.755700",
            }
        ],
    }

    slack_change_resource_page(payload, body)

    # Trigger id should be the same as in the body
    assert cache.get("slack_view_id") == "xx"
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "dialog:resource",
        "title": {"type": "plain_text", "text": "Resource", "emoji": True},
        "blocks": [
            {
                "type": "actions",
                "block_id": "change_resource_page",
                "elements": [
                    {
                        "type": "static_select",
                        "action_id": "change_resource_page",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select chapter",
                            "emoji": True,
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": resource_user1.resource.chapters.first().name,  # noqa
                                    "emoji": True,
                                },
                                "value": str(
                                    resource_user1.resource.chapters.first().id
                                ),
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": resource_user1.resource.chapters.last().name,  # noqa
                                    "emoji": True,
                                },
                                "value": str(
                                    resource_user1.resource.chapters.last().id
                                ),
                            },
                        ],
                    }
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{resource_user1.resource.chapters.last().name}*",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "This is the second page"},
            },
        ],
    }


@pytest.mark.django_db
def test_show_to_do_items(new_hire_factory, to_do_user_factory):
    new_hire1 = new_hire_factory(slack_user_id="slackx")
    new_hire2 = new_hire_factory()
    new_hire_factory(slack_user_id="slacky")

    to_do_user1 = to_do_user_factory(user=new_hire1)
    to_do_user2 = to_do_user_factory(user=new_hire1)
    to_do_user3 = to_do_user_factory(user=new_hire1)
    to_do_user_factory(user=new_hire2)

    body = {"user": {"id": "slackx"}}
    slack_show_to_do_items(body)

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user1.to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user1.id),
                "action_id": f"dialog:to_do:{to_do_user1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user2.to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user2.id),
                "action_id": f"dialog:to_do:{to_do_user2.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user3.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user3.to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user3.id),
                "action_id": f"dialog:to_do:{to_do_user3.id}",
            },
        },
    ]

    body = {"user": {"id": "slacky"}}
    slack_show_to_do_items(body)

    assert cache.get("slack_channel") == "slacky"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "I couldn't find any tasks."},
        }
    ]


@pytest.mark.django_db
def test_complete_to_do(new_hire_factory, to_do_user_factory):
    new_hire1 = new_hire_factory(slack_user_id="slackx", slack_channel_id="slackx")

    to_do_user1 = to_do_user_factory(user=new_hire1)
    to_do_user2 = to_do_user_factory(user=new_hire1)

    body = {
        "type": "view_submission",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "api_app_id": "xx",
        "token": "xxx",
        "trigger_id": "sdf187e7bd520edc82a3cb",
        "view": {
            "id": "view_idxx",
            "team_id": "xx",
            "type": "modal",
            "blocks": to_do_user1.to_do.to_slack_block(new_hire1),
            "private_metadata": '{"to_do_ids_from_original_message": ["'
            + str(to_do_user1.id)
            + '", "'
            + str(to_do_user2.id)
            + '"], "text": "These are the tasks you need to complete:", "to_do_id": '
            + str(to_do_user1.id)
            + ', "message_ts": "1653088141.676019"}',
            "callback_id": "complete:to_do",
            "state": {"values": {}},
            "hash": "165309021AoR3iSS",
            "title": {
                "type": "plain_text",
                "text": to_do_user1.to_do.name,
                "emoji": True,
            },
            "clear_on_close": False,
            "notify_on_close": False,
            "close": None,
            "submit": {"type": "plain_text", "text": "done", "emoji": True},
            "previous_view_id": None,
            "root_view_id": "ssssddd",
            "app_id": "xx",
            "external_id": "",
            "app_installed_team_id": "xxx",
            "bot_id": "xxkdf",
        },
        "response_urls": [],
        "is_enterprise_install": False,
        "enterprise": None,
    }

    view = {
        "id": "V03GE5HD55H",
        "team_id": "T7R4ZPZ1C",
        "type": "modal",
        "blocks": to_do_user1.to_do.to_slack_block(new_hire1),
        "private_metadata": '{"to_do_ids_from_original_message": ["'
        + str(to_do_user1.id)
        + '", "'
        + str(to_do_user2.id)
        + '"], "text": "These are the tasks you need to complete:", "to_do_id": '
        + str(to_do_user1.id)
        + ', "message_ts": "1653088141.676019"}',
        "callback_id": "complete:to_do",
        "state": {"values": {}},
        "hash": "165309021oR3iSS",
        "title": {"type": "plain_text", "text": to_do_user1.to_do.name, "emoji": True},
        "clear_on_close": False,
        "notify_on_close": False,
        "close": None,
        "submit": {"type": "plain_text", "text": "done", "emoji": True},
        "previous_view_id": None,
        "root_view_id": "xxxkd",
        "app_id": "sxklsdf",
        "external_id": "",
        "app_installed_team_id": "slksd",
        "bot_id": "B03CWBH49NW",
    }
    slack_complete_to_do(body, view)

    assert cache.get("slack_channel") == "slackx"
    # First item is gone
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user2.to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user2.id),
                "action_id": f"dialog:to_do:{to_do_user2.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_resource_next_page(new_hire_factory, resource_user_factory, chapter_factory):
    new_hire1 = new_hire_factory(slack_user_id="slackx")

    resource_user1 = resource_user_factory(user=new_hire1)
    resource_user_factory(user=new_hire1)
    chapter1 = chapter_factory(
        resource=resource_user1.resource,
        type=0,
        content={
            "time": 0,
            "blocks": [{"data": {"text": "first page"}, "type": "paragraph"}],
        },
        order=0,
    )
    chapter2 = chapter_factory(
        resource=resource_user1.resource,
        type=0,
        content={
            "time": 0,
            "blocks": [{"data": {"text": "second page"}, "type": "paragraph"}],
        },
        order=1,
    )
    resource_user1.resource.chapters.set([chapter1, chapter2])

    mock = Mock()
    body = {
        "type": "view_submission",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "view": {
            "hash": "F8VrpY",
            "id": "id",
        },
    }
    view = {
        "id": "id",
        "team_id": "team",
        "type": "modal",
        "blocks": chapter1.to_slack_block(resource_user1.user),
        "private_metadata": '{"current_chapter": '
        + str(chapter1.id)
        + ', "resource_user": '
        + str(resource_user1.id)
        + "}",
        "callback_id": "dialog:resource",
        "state": {"values": {}},
        "hash": "F8VrpY",
        "title": {"type": "plain_text", "text": "Course", "emoji": True},
        "clear_on_close": False,
        "notify_on_close": False,
        "close": None,
        "submit": {"type": "plain_text", "text": "Next", "emoji": True},
        "previous_view_id": None,
        "root_view_id": "roklsdf",
        "app_id": "xx",
        "external_id": "",
        "app_installed_team_id": "xxx",
        "bot_id": "xxx",
    }
    slack_next_page_resource(mock, body, view)
    assert cache.get("slack_view_id") == "id"
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "dialog:resource",
        "title": {"type": "plain_text", "text": "Course", "emoji": True},
        "private_metadata": '{"current_chapter": '
        + str(chapter2.id)
        + ', "resource_user": '
        + str(resource_user1.id)
        + "}",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{chapter2.name}*"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": "second page"}},
        ],
    }


@pytest.mark.django_db
def test_show_welcome_dialog(new_hire_factory):
    new_hire1 = new_hire_factory(slack_user_id="slackx")
    body = {
        "type": "block_actions",
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "trigger_id": "test",
    }
    payload = {
        "action_id": "dialog:welcome",
        "block_id": "vbAYi",
        "text": {
            "type": "plain_text",
            "text": "Welkom deze nieuwe medewerker!",
            "emoji": True,
        },
        "value": str(new_hire1.id),
        "style": "primary",
        "type": "button",
        "action_ts": "1653432200.902062",
    }

    slack_show_welcome_dialog(body, payload)
    assert cache.get("slack_trigger_id") == "test"
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "save:welcome",
        "title": {"type": "plain_text", "text": "Welcome this new hire!"},
        "submit": {"type": "plain_text", "text": "Submit"},
        "blocks": [
            {
                "block_id": "input",
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "message",
                },
                "label": {
                    "type": "plain_text",
                    "text": "What would you like to say to our new hire?",
                },
            }
        ],
        "private_metadata": '{"user_id": "' + str(new_hire1.id) + '"}',
    }


@pytest.mark.django_db
def test_save_welcome_message(new_hire_factory):
    new_hire1 = new_hire_factory(slack_user_id="slackx")
    body = {
        "type": "view_submission",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "response_urls": [],
        "is_enterprise_install": False,
        "enterprise": None,
    }
    view = {
        "id": "xxxxxk",
        "team_id": "slkd",
        "type": "modal",
        "private_metadata": '{"user_id": "' + str(new_hire1.id) + '"}',
        "callback_id": "save:welcome",
        "state": {
            "values": {
                "input": {
                    "message": {
                        "type": "plain_text_input",
                        "value": "Example welcome message",
                    }
                }
            }
        },
        "hash": "2201.wea5M6dz",
        "external_id": "",
        "app_installed_team_id": "xx",
        "bot_id": "xx",
    }
    slack_save_welcome_message(body, view)

    assert (
        cache.get("slack_text")
        == 'Message has been saved! Your message: "Example welcome message"'
    )


@pytest.mark.django_db
def test_join_user_auto_create_without_approval(sequence_factory, to_do_factory):
    # Create sequence to be added automatically
    sequence = sequence_factory(auto_add=True)
    to_do = to_do_factory()
    condition = sequence.conditions.first()
    condition.to_do.add(to_do)

    # Enable both create user and automatically add as a new hire
    org = Organization.object.get()
    org.auto_create_user = True
    org.create_new_hire_without_confirm = True
    org.save()

    event = {
        "type": "team_join",
        "user": {
            "id": "xxx",
            "team_id": "xxx",
            "name": "hi",
            "deleted": False,
            "color": "d58247",
            "real_name": "Peter Boom",
            "tz": "Europe/Amsterdam",
            "tz_label": "Central European Summer Time",
            "tz_offset": 7200,
            "profile": {
                "title": "",
                "phone": "",
                "skype": "",
                "real_name": "Peter Boom",
                "real_name_normalized": "Peter Boom",
                "display_name": "Peter Boom",
                "display_name_normalized": "Peter Boom",
                "fields": None,
                "status_text": "",
                "status_emoji": "",
                "status_emoji_display_info": [],
                "status_expiration": 0,
                "avatar_hash": "g73e8d744a4c",
                "email": "hi@chiefonboarding.com",
                "first_name": "Peter",
                "last_name": "Boom",
                "team": "T7R4ZPZ1C",
            },
            "is_admin": False,
            "is_owner": False,
            "is_primary_owner": False,
            "is_restricted": False,
            "is_ultra_restricted": False,
            "is_bot": False,
            "is_app_user": False,
            "updated": 1653440565,
            "is_email_confirmed": True,
            "who_can_share_contact_card": "EVERYONE",
            "presence": "away",
        },
        "cache_ts": 1653440565,
        "event_ts": "1653440565.001100",
    }
    slack_create_new_hire_or_ask_perm(event)
    assert get_user_model().objects.count() == 1
    user = get_user_model().objects.first()
    # To do item from sequence
    assert user.to_do.count() == 1
    assert user.role == 0
    assert user.is_active


@pytest.mark.django_db
def test_join_user_auto_create_with_request_for_approval(admin_factory):
    # Enable both create user and automatically add as a new hire
    admin = admin_factory(slack_user_id="slackx")

    org = Organization.object.get()
    org.auto_create_user = True
    org.create_new_hire_without_confirm = False
    org.slack_confirm_person = admin
    org.save()

    event = {
        "type": "team_join",
        "user": {
            "id": "xxx",
            "team_id": "xxx",
            "name": "hi",
            "deleted": False,
            "color": "d58247",
            "real_name": "Peter Boom",
            "tz": "Europe/Amsterdam",
            "tz_label": "Central European Summer Time",
            "tz_offset": 7200,
            "profile": {
                "title": "",
                "phone": "",
                "skype": "",
                "real_name": "Peter Boom",
                "real_name_normalized": "Peter Boom",
                "display_name": "Peter Boom",
                "display_name_normalized": "Peter Boom",
                "fields": None,
                "status_text": "",
                "status_emoji": "",
                "status_emoji_display_info": [],
                "status_expiration": 0,
                "avatar_hash": "g73e8d744a4c",
                "email": "hi@chiefonboarding.com",
                "first_name": "Peter",
                "last_name": "Boom",
                "team": "T7R4ZPZ1C",
            },
            "is_admin": False,
            "is_owner": False,
            "is_primary_owner": False,
            "is_restricted": False,
            "is_ultra_restricted": False,
            "is_bot": False,
            "is_app_user": False,
            "updated": 1653440565,
            "is_email_confirmed": True,
            "who_can_share_contact_card": "EVERYONE",
            "presence": "away",
        },
        "cache_ts": 1653440565,
        "event_ts": "1653440565.001100",
    }
    slack_create_new_hire_or_ask_perm(event)
    # Both admin and user exist
    assert get_user_model().objects.count() == 2
    new_hire = get_user_model().objects.last()
    # New hire is not active
    assert new_hire.role == 3
    assert not new_hire.is_active

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Would you like to put this new hire through onboarding?\n*Name:* Peter Boom ",  # noqa
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Yeah!"},
                    "style": "primary",
                    "value": str(new_hire.id),
                    "action_id": "create:newhire:approve",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Nope"},
                    "style": "danger",
                    "value": "-1",
                    "action_id": "create:newhire:deny",
                },
            ],
        },
    ]


@pytest.mark.django_db
def test_open_modal_for_selecting_sequences_approved_new_hire(
    new_hire_factory, admin_factory
):
    admin_factory(slack_user_id="slackx")
    new_hire = new_hire_factory()
    body = {
        "type": "block_actions",
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "api_app_id": "xx",
        "token": "xxx",
        "container": {
            "type": "message",
            "message_ts": "3492363.887579",
            "channel_id": "xxx",
            "is_ephemeral": False,
        },
        "trigger_id": "dkfd0eec0a0d3877827bb50bf2fae281",
        "state": {"values": {}},
    }
    payload = {
        "action_id": "create:newhire:approve",
        "block_id": "ZZ1Mf",
        "text": {"type": "plain_text", "text": "Yeah!", "emoji": True},
        "value": str(new_hire.id),
        "style": "primary",
        "type": "button",
        "action_ts": "1653493687.010067",
    }

    slack_open_modal_for_selecting_seq_item(body, payload)

    assert cache.get("slack_trigger_id") == body["trigger_id"]
    assert cache.get("slack_view") == {
        "type": "modal",
        "callback_id": "approve:newhire",
        "title": {"type": "plain_text", "text": "New hire options"},
        "submit": {"type": "plain_text", "text": "Create new hire"},
        "blocks": [
            {
                "type": "input",
                "block_id": "seq",
                "label": {"type": "plain_text", "text": "Select sequences"},
                "element": {
                    "type": "multi_static_select",
                    "placeholder": {"type": "plain_text", "text": "Select sequences"},
                    "options": [],
                    "action_id": "answers",
                },
            }
        ],
        "private_metadata": '{"user_id": "'
        + str(new_hire.id)
        + '", "ts": "3492363.887579"}',
    }


@pytest.mark.django_db
def test_adding_selecting_sequences_approved_new_hire(
    new_hire_factory, sequence_factory, admin_factory
):
    seq = sequence_factory()
    new_hire = new_hire_factory(slack_user_id="slackx")

    admin = admin_factory(slack_channel_id="slacky")
    org = Organization.object.get()
    org.slack_confirm_person = admin
    org.save()

    body = {
        "type": "view_submission",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "user": {
            "id": "slackx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "api_app_id": "xx",
        "token": "xxx",
        "trigger_id": "xxxxxxx",
        "view": {
            "id": "xx",
            "team_id": "xx",
            "type": "modal",
            "private_metadata": '{"user_id": "'
            + str(new_hire.id)
            + '", "ts": "1653492363.887579"}',
            "callback_id": "approve:newhire",
            "state": {
                "values": {
                    "seq": {
                        "answers": {
                            "type": "multi_static_select",
                            "selected_options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "New sequence1",
                                        "emoji": True,
                                    },
                                    "value": str(seq.id),
                                }
                            ],
                        }
                    }
                }
            },
            "hash": "1653495403.s",
            "title": {"type": "plain_text", "text": "New hire options", "emoji": True},
            "clear_on_close": False,
            "notify_on_close": False,
            "close": None,
            "submit": {"type": "plain_text", "text": "Create new hire", "emoji": True},
            "previous_view_id": None,
            "root_view_id": "xx",
            "app_id": "xx",
            "external_id": "",
            "app_installed_team_id": "xx",
            "bot_id": "xx",
        },
        "response_urls": [],
        "is_enterprise_install": False,
        "enterprise": None,
    }

    view = {
        "id": "xx",
        "team_id": "xx",
        "type": "modal",
        "blocks": [
            {
                "type": "input",
                "block_id": "seq",
                "label": {
                    "type": "plain_text",
                    "text": "Select sequences",
                    "emoji": True,
                },
                "optional": False,
                "dispatch_action": False,
                "element": {
                    "type": "multi_static_select",
                    "action_id": "answers",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select sequences",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "sss",
                                "emoji": True,
                            },
                            "value": str(seq.id),
                        },
                    ],
                },
            }
        ],
        "private_metadata": '{"user_id": "'
        + str(new_hire.id)
        + '", "ts": "1653492363.887579"}',
        "callback_id": "approve:newhire",
        "state": {
            "values": {
                "seq": {
                    "answers": {
                        "type": "multi_static_select",
                        "selected_options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "New sequence1",
                                    "emoji": True,
                                },
                                "value": str(seq.id),
                            }
                        ],
                    }
                }
            }
        },
        "hash": "1653495403.zjdTDzCH",
        "title": {"type": "plain_text", "text": "New hire options", "emoji": True},
        "clear_on_close": False,
        "notify_on_close": False,
        "close": None,
        "submit": {"type": "plain_text", "text": "Create new hire", "emoji": True},
        "previous_view_id": None,
        "root_view_id": "V03HNUKADT2",
        "app_id": "A03CWAH7L91",
        "external_id": "",
        "app_installed_team_id": "T7R4ZPZ1C",
        "bot_id": "B03CWBH49NW",
    }

    slack_add_sequences_to_new_hire(body, view)

    assert cache.get("slack_channel") == "slacky"
    assert cache.get("slack_ts") == "1653492363.887579"
    assert cache.get("slack_blocks") == []
    assert (
        cache.get("slack_text")
        == "You approved the request to onboard " + new_hire.full_name
    )


@pytest.mark.django_db
def test_deny_new_hire(admin_factory):
    admin = admin_factory(slack_channel_id="slacky")
    org = Organization.object.get()
    org.slack_confirm_person = admin
    org.save()

    body = {
        "type": "block_actions",
        "user": {
            "id": "xx",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "api_app_id": "xx",
        "token": "xxx",
        "container": {
            "type": "message",
            "message_ts": "1653515878.620089",
            "channel_id": "xx",
            "is_ephemeral": False,
        },
        "trigger_id": "343e8837f808e9fed5ded71bd8f4",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "enterprise": None,
        "is_enterprise_install": False,
        "channel": {"id": "x", "name": "directmessage"},
        "state": {"values": {}},
        "actions": [
            {
                "action_id": "create:newhire:deny",
                "block_id": "FOQJd",
                "text": {"type": "plain_text", "text": "Nope", "emoji": True},
                "value": "-1",
                "style": "danger",
                "type": "button",
                "action_ts": "1653516036.098177",
            }
        ],
    }
    slack_deny_new_hire(body)

    assert cache.get("slack_channel") == "slacky"
    assert cache.get("slack_ts") == "1653515878.620089"
    assert cache.get("slack_blocks") == []
    assert cache.get("slack_text") == "You denied the request to onboard this person."


@pytest.mark.django_db
def test_complete_admin_task(admin_factory, admin_task_factory):
    admin_task = admin_task_factory()
    admin_factory(slack_user_id="slacky", slack_channel_id="xx")

    body = {
        "type": "block_actions",
        "user": {
            "id": "slacky",
            "username": "hello",
            "name": "hello",
            "team_id": "xx",
        },
        "api_app_id": "xx",
        "token": "xxx",
        "container": {
            "type": "message",
            "message_ts": "1653519601.452689",
            "channel_id": "xx",
            "is_ephemeral": False,
        },
        "trigger_id": "df5b9460bddc17e2398d12098b41b7a",
        "team": {"id": "xx", "domain": "chiefonboarding"},
        "enterprise": None,
        "is_enterprise_install": False,
        "state": {"values": {}},
        "actions": [
            {
                "action_id": "admin_task:complete",
                "block_id": "XUmz",
                "text": {
                    "type": "plain_text",
                    "text": "I have completed this",
                    "emoji": True,
                },
                "value": str(admin_task.id),
                "style": "primary",
                "type": "button",
                "action_ts": "1653520440.451239",
            }
        ],
    }
    payload = {
        "action_id": "admin_task:complete",
        "block_id": "XUmz",
        "text": {"type": "plain_text", "text": "I have completed this", "emoji": True},
        "value": str(admin_task.id),
        "style": "primary",
        "type": "button",
        "action_ts": "1653520440.451239",
    }
    slack_complete_admin_task(body, payload)

    assert cache.get("slack_channel") == "xx"
    assert cache.get("slack_ts") == "1653519601.452689"
    assert cache.get("slack_blocks") == []
    assert cache.get("slack_text") == "Thanks! This has been marked as completed."
    admin_task.refresh_from_db()
    assert admin_task.completed


# TEST TASKS
@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.find_by_email", Mock(return_value={"user": {"id": "slackx"}})
)
def test_link_slack_users_slack_not_enabled(new_hire_factory, integration_factory):
    new_hire = new_hire_factory()

    # Gets blocked imidiately for not having Slack enabled
    link_slack_users()

    new_hire.refresh_from_db()
    assert new_hire.slack_user_id == ""

    # Add integration
    integration_factory(integration=0)

    link_slack_users()

    new_hire.refresh_from_db()
    assert new_hire.slack_user_id == "slackx"


@pytest.mark.django_db
@patch("slack_bot.utils.Slack.find_by_email", Mock(return_value=False))
def test_link_slack_users_not_found(new_hire_factory, integration_factory):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory()

    link_slack_users()

    new_hire.refresh_from_db()
    assert new_hire.slack_user_id == ""


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.find_by_email", Mock(return_value={"user": {"id": "slackx"}})
)
def test_link_slack_users_send_welcome_message_without_to_dos(
    new_hire_factory, integration_factory, introduction_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory()
    # Test personalizing message
    wm = WelcomeMessage.objects.get(language=new_hire.language, message_type=3)
    wm.message += " {{first_name}}"
    wm.save()

    # Add an introduction message to show
    intro = introduction_factory()
    new_hire.introductions.add(intro)

    # Add a todo message to show
    # to_do_user = to_do_user_factory(user=new_hire, to_do__due_on_day=1)

    link_slack_users()

    assert cache.get("slack_channel", "") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": wm.message.split(" ")[0] + " " + new_hire.first_name,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Click a button to see more information :)",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "To do items"},
                    "action_id": "show_to_do_items",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Resources"},
                    "action_id": "show_resource_items",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{intro.name}:* {intro.intro_person.full_name}\n{intro.intro_person.position}\n_Hi {new_hire.first_name}, how is it going? Great to have you with us!_\n{intro.intro_person.email} ",  # noqa
            },
        },
    ]


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.find_by_email", Mock(return_value={"user": {"id": "slackx"}})
)
def test_link_slack_users_send_welcome_message_with_to_dos(
    new_hire_factory, integration_factory, introduction_factory, to_do_user_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory()
    # Test personalizing message
    wm = WelcomeMessage.objects.get(language=new_hire.language, message_type=3)
    wm.message += " {{first_name}}"
    wm.save()

    # Add an introduction message to show
    intro = introduction_factory()
    new_hire.introductions.add(intro)

    # Add a todo message to show
    to_do_user = to_do_user_factory(user=new_hire, to_do__due_on_day=1)

    link_slack_users()

    assert cache.get("slack_channel", "") == "slackx"
    assert cache.get("slack_blocks", "") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These are the tasks you need to complete:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user.id),
                "action_id": f"dialog:to_do:{to_do_user.id}",
            },
        },
    ]


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.find_by_email", Mock(return_value={"user": {"id": "slackx"}})
)
def test_link_slack_users_only_send_once(new_hire_factory, integration_factory):
    # Enable Slack
    integration_factory(integration=0)

    new_hire_factory(slack_user_id="slackx")
    link_slack_users()

    # Shouldn't triggered the "send message" function
    assert cache.get("slack_channel", "") == ""


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_update_new_hire_without_valid_slack(new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    # One to do item that is over due and one that's not due yet
    to_do_user_factory(user=new_hire, to_do__due_on_day=3)

    update_new_hire()

    # Don't send anything, no valid integration found
    assert cache.get("slack_channel", "") == ""


@pytest.mark.django_db
@freeze_time("2022-05-13 09:00:00")
def test_update_new_hire_not_valid_time(
    new_hire_factory, integration_factory, to_do_user_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    # One to do item that is over due and one that's not due yet
    to_do_user_factory(user=new_hire, to_do__due_on_day=3)

    update_new_hire()

    assert cache.get("slack_channel", "") == ""


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_update_new_hire_with_to_do_updates(
    new_hire_factory, integration_factory, to_do_user_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    # One to do item that is over due and one that's not due yet
    # to_do_user1 = to_do_user_factory(user=new_hire, to_do__due_on_day=1)
    to_do_user1 = to_do_user_factory(user=new_hire, to_do__due_on_day=3)

    # Also create one that is already completed
    to_do_user_factory(user=new_hire, to_do__due_on_day=1, completed=True)

    update_new_hire()

    assert cache.get("slack_channel") == "slackx"
    assert (
        cache.get("slack_text")
        == "Good morning! These are the tasks you need to complete today:"
    )
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Good morning! These are the tasks you need to complete today:",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user1.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user1.id),
                "action_id": f"dialog:to_do:{to_do_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
@freeze_time("2022-05-13 09:00:00")
def test_update_new_hire_with_to_do_updates_outside_8am(
    new_hire_factory, integration_factory, to_do_user_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    # One to do item that is over due and one that's not due yet
    to_do_user_factory(user=new_hire, to_do__due_on_day=1)
    to_do_user_factory(user=new_hire, to_do__due_on_day=3)

    # Also create one that is already completed
    to_do_user_factory(user=new_hire, to_do__due_on_day=1, completed=True)

    update_new_hire()

    assert cache.get("slack_channel", "") == ""


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_update_new_hire_with_to_do_updates_overdue(
    new_hire_factory, integration_factory, to_do_user_factory
):
    # Enable Slack
    integration_factory(integration=0)

    new_hire = new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    # One to do item that is over due and one that's not due yet
    to_do_user1 = to_do_user_factory(user=new_hire, to_do__due_on_day=1)
    to_do_user2 = to_do_user_factory(user=new_hire, to_do__due_on_day=3)

    # Also create one that is already completed
    to_do_user_factory(user=new_hire, to_do__due_on_day=1, completed=True)

    update_new_hire()

    assert cache.get("slack_channel") == "slackx"
    assert (
        cache.get("slack_text")
        == "Good morning! These are the tasks you need to complete. Some to do items are overdue. Please complete those as soon as possible!"  # noqa
    )
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Good morning! These are the tasks you need to complete. Some to do items are overdue. Please complete those as soon as possible!",  # noqa
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user1.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user1.id),
                "action_id": f"dialog:to_do:{to_do_user1.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_user2.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user2.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user2.id),
                "action_id": f"dialog:to_do:{to_do_user2.id}",
            },
        },
    ]


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_first_day_reminder(new_hire_factory, integration_factory):
    org = Organization.object.get()
    org.send_new_hire_start_reminder = False
    org.save()

    # Enable Slack
    integration_factory(integration=0)

    new_hire1 = new_hire_factory(
        start_day=datetime.now().date(), slack_user_id="slackx"
    )
    new_hire2 = new_hire_factory(start_day=datetime.now().date())

    new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2), slack_user_id="slackx"
    )

    first_day_reminder()

    # Will not send since `send_new_hire_start_reminder` is disabled
    assert cache.get("slack_channel", "") == ""

    org.send_new_hire_start_reminder = True
    org.save()

    first_day_reminder()

    assert cache.get("slack_channel") == "#general"
    assert (
        cache.get("slack_text")
        == f"We got some new hires coming in! {new_hire1.full_name}, {new_hire2.full_name} are starting today!"  # noqa
    )

    # Set one new hire back to check text if one new hire is starting
    new_hire1.start_day = datetime.now().date() - timedelta(days=2)
    new_hire1.save()

    first_day_reminder()

    assert cache.get("slack_channel") == "#general"
    assert (
        cache.get("slack_text")
        == f"Just a quick reminder: It's {new_hire2.full_name}'s first day today!"
    )


@pytest.mark.django_db
def test_birthday_reminder(new_hire_factory, integration_factory):
    org = Organization.object.get()
    org.slack_birthday_wishes_channel = None
    org.save()

    # Enable Slack
    integration_factory(integration=0)

    new_hire1 = new_hire_factory(
        start_day=datetime.now().date(),
        slack_user_id="slackx",
        birthday=datetime.now().date(),
    )
    new_hire_factory(start_day=datetime.now().date(), birthday=datetime(2022, 5, 20))

    birthday_reminder()

    # Will not send since `birthday_wishes` is disabled
    assert cache.get("slack_channel", "") == ""

    sc = SlackChannel.objects.create(name="general")
    org.slack_birthday_wishes_channel = sc
    org.save()

    birthday_reminder()

    assert cache.get("slack_channel") == "#general"
    assert cache.get("slack_text") == f"It's {new_hire1.full_name}'s birthday today!"


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_introduce_new_hire(new_hire_factory, integration_factory):
    org = Organization.object.get()
    org.ask_colleague_welcome_message = False
    org.save()

    # Enable Slack
    integration_factory(integration=0)

    # Will not send since `ask_colleague_welcome_message` is disabled
    introduce_new_people()
    assert cache.get("slack_channel", "") == ""

    org.ask_colleague_welcome_message = True
    org.save()

    # Will not send since there are no new hires to introduce
    introduce_new_people()
    assert cache.get("slack_channel", "") == ""

    # Create a new hire
    new_hire1 = new_hire_factory(
        slack_user_id="slackx",
        start_day=datetime.now().date(),
        message="This is our new hire Stan. He loves coding.",
    )
    # Create a new hire with a start day in the past - not shown
    new_hire_factory(
        slack_user_id="slackx", start_day=datetime.now().date() - timedelta(days=2)
    )

    # This one is already introduced, should not introduced again
    new_hire_factory(
        start_day=datetime.now().date() - timedelta(days=2),
        slack_user_id="slackx",
        is_introduced_to_colleagues=True,
    )

    introduce_new_people()

    assert cache.get("slack_channel") == "#general"

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"We have a new hire coming in soon! Make sure to leave a message for {new_hire1.first_name}!",  # noqa: E501
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{new_hire1.full_name}*\n_{new_hire1.message}_",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{new_hire1.first_name} starts on {localize(new_hire1.start_day)}.",  # noqa: E501
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Welcome this new hire!"},
                    "style": "primary",
                    "value": str(new_hire1.id),
                    "action_id": "dialog:welcome",
                }
            ],
        },
    ]

    # Introduce two new hires
    new_hire3 = new_hire_factory(
        message="This is our new hire Paul. He is vegan.", position="Developer"
    )
    new_hire4 = new_hire_factory(start_day=datetime.now().date())

    introduce_new_people()

    # Should not show the already introduced ones, but only the new ones
    assert cache.get("slack_channel") == "#general"

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "We got some new hires coming in soon! Make sure to leave a welcome message for them!",  # noqa
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{new_hire3.full_name}*\n_This is our new hire Paul. He is vegan._",  # noqa
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{new_hire3.first_name} starts on {localize(new_hire3.start_day)} and is our new {new_hire3.position}.",  # noqa
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Welcome this new hire!"},
                    "style": "primary",
                    "value": str(new_hire3.id),
                    "action_id": "dialog:welcome",
                }
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{new_hire4.full_name}*"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{new_hire4.first_name} starts on May 13, 2022.",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Welcome this new hire!"},
                    "style": "primary",
                    "value": str(new_hire4.id),
                    "action_id": "dialog:welcome",
                }
            ],
        },
    ]
