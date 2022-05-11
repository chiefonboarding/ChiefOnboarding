import json
from datetime import datetime, timedelta

import pytest
from django.core.cache import cache

from slack_bot.views import (
    slack_catch_all_message_search_resources,
    slack_open_modal_for_selecting_seq_item,
    slack_open_todo_dialog,
    slack_show_all_resources_categories,
    slack_show_help,
    slack_show_resources_items_in_category,
    slack_show_to_do_items_based_on_message,
)
from users.factories import ResourceUserFactory


@pytest.fixture
def incomming_message_payload():
    return {
        "token": "xxxxxx",
        "team_id": "T061EG3I6",
        "api_app_id": "A0P343K2",
        "event": {
            "type": "message",
            "channel": "D0243491L",
            "user": "U2147483497",
            "text": "show me to do items",
            "ts": "1355514523.000005",
            "event_ts": "133417523.000005",
            "channel_type": "im",
        },
        "type": "event_callback",
        "authed_teams": ["T061349R6"],
        "event_id": "Ev0P342K21",
        "event_time": 13553437523,
    }


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

    resource_user1 = resource_user_factory(resource__category=None, user=new_hire)
    resource_user2 = resource_user_factory(resource__category=None, user=new_hire)

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
            "block_id": str(to_do_due_in_past1.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past1.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past1.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past1.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past2.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past2.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past2.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past2.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today1.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today1.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today1.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_today1.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today2.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today2.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today2.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_today2.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_future1.to_do.id),
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
                "value": str(to_do_due_future1.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_future1.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_future2.to_do.id),
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
                "value": str(to_do_due_future2.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_future2.to_do.id}",
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
            "block_id": str(to_do_due_today1.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today1.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today1.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_today1.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_today2.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_today2.to_do.name}*\nThis task is due today",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_today2.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_today2.to_do.id}",
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
            "block_id": str(to_do_due_in_past1.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past1.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past1.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past1.to_do.id}",
            },
        },
        {
            "type": "section",
            "block_id": str(to_do_due_in_past2.to_do.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_due_in_past2.to_do.name}*\nThis task is overdue",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_due_in_past2.to_do.id),
                "action_id": f"dialog:to_do:{to_do_due_in_past2.to_do.id}",
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
        {"action_id": f"dialog:to_do:{to_do_user1.to_do.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 0,
            "container": {"message_ts": 0},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": 1, "text": {"text": "Here are the todo items:"}},
                    {"block_id": to_do_user1.to_do.id},
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
                "to_do_ids_from_original_message": [to_do_user1.to_do.id],
                "text": "Here are the todo items:",
                "to_do_id": to_do_user1.to_do.id,
                "message_ts": 0,
            }
        ),
    }


@pytest.mark.django_db
def test_slack_to_do_complete_external_form(new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(slack_user_id="slackx")

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
        {"action_id": f"dialog:to_do:{to_do_user1.to_do.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 21212,
            "containers": {"message_ts": 23123},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": "1", "text": {"text": "Here are the todo items:"}},
                    {"block_id": str(to_do_user1.to_do.id)},
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
    to_do_user1.save()

    # Reclick the button
    slack_open_todo_dialog(
        {"action_id": f"dialog:to_do:{to_do_user1.to_do.id}"},
        {
            "user": {"id": "slackx"},
            "trigger_id": 21212,
            "containers": {"message_ts": 23123},
            "message": {
                "text": "Here are the todo items:",
                "blocks": [
                    {"block_id": "1", "text": {"text": "Here are the todo items:"}},
                    {"block_id": str(to_do_user1.to_do.id)},
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
