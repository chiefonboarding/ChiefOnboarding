import json
import logging
import re
from unittest.mock import Mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from sentry_sdk import capture_exception
from slack_bolt import App as SlackBoltApp

from admin.admin_tasks.models import AdminTask
from admin.integrations.models import Integration
from admin.resources.models import Category, Chapter, CourseAnswer, Resource
from admin.sequences.models import Sequence
from organization.models import Organization, Notification
from users.models import NewHireWelcomeMessage, ResourceUser, ToDoUser

from .slack_misc import get_new_hire_approve_sequence_options
from .slack_resource import SlackResource, SlackResourceCategory
from .slack_to_do import SlackToDo, SlackToDoManager
from .utils import Slack, actions, button, paragraph

logger = logging.getLogger(__name__)

if settings.RUNNING_TESTS:
    app = Mock()
else:
    if settings.SLACK_USE_SOCKET:
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        app = SlackBoltApp(
            token=settings.SLACK_BOT_TOKEN,
            logger=logger,
            raise_error_for_unhandled_request=True,
        )

        slack_handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        slack_handler.connect()
    else:
        integration = Integration.objects.filter(integration=0).first()
        app = SlackBoltApp(
            token=integration.token, signing_secret=integration.signing_secret
        )


def exception_handler(func):
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
            capture_exception(e)

    return inner_function


def no_bot_messages(message) -> bool:
    return message.get("subtype") != "bot_message" and (
        "message" not in message or "bot_id" not in message.get("message")
    )

def message_changed_matcher(message) -> bool:
    return message.get("subtype", "") == "message_changed"


@exception_handler
@app.error
def custom_error_handler(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")


@exception_handler
@app.message(re.compile("(help)"), matchers=[no_bot_messages])
def show_help(message):
    slack_show_help(message)


def slack_show_help(message):
    # user = get_user(message["user"])
    # if user is None:
    #     return

    messages = [
        _("Happy to help! Here are all the things you can say to me: \n\n"),
        _(
            "*What do I need to do today?*\nThis will show all the tasks you need "
            "to do today. I will show you these every day as well, but just incase "
            "you want to get them again.\n"
        ),
        _(
            "*Do I have any to do items that are overdue?*\nThis will show all "
            "tasks that should have been completed. Please do those as soon as "
            "possible.\n"
        ),
        _("*Show me all to do items*\nThis will show all tasks\n"),
        _("*Show me all resources*\nThis will show all resources."),
    ]

    Slack().send_message(text="".join(messages), channel=message["user"])


def get_user(slack_user_id):
    users = get_user_model().objects.filter(slack_user_id=slack_user_id)
    if users.exists():
        translation.activate(users.first().language)
        return users.first()
    else:
        Slack().send_message(
            text=_(
                "You don't seem to be setup yet. Please ask your supervisor for access."
            ),
            channel=slack_user_id,
        )


@exception_handler
@app.event("message", matchers=[message_changed_matcher])
def message_changed(body):
    try:
        user = get_user_model().objects.get(slack_channel_id=body["channel"])
    except get_user_model().DoesNotExist:
        return

    Notification.objects.create(
        notification_type="updated_slack_message",
        extra_text=body.get("message", {}).get("text", ""),
        created_for=user,
        blocks=body.get("message", {}).get("blocks", []),
    )


@exception_handler
@app.message(re.compile("(resource)"), matchers=[no_bot_messages])
def show_all_resources_categories(message):
    slack_show_all_resources_categories(message)


def slack_show_all_resources_categories(message):
    user = get_user(message["user"])
    if user is None:
        return
    blocks = SlackResourceCategory(user=user).category_buttons()
    Slack().send_message(
        text=_("Select a category:"), blocks=blocks, channel=message["user"]
    )


@exception_handler
@app.message(re.compile("(to do|todo|todos)"), matchers=[no_bot_messages])
def show_to_do_items_based_on_message(message):
    slack_show_to_do_items_based_on_message(message)


def slack_show_to_do_items_based_on_message(message):
    user = get_user(message["user"])
    if user is None:
        return

    items = ToDoUser.objects.all_to_do(user)
    if _("today") in message["text"]:
        items = ToDoUser.objects.due_today(user)
    if _("overdue") in message["text"]:
        items = ToDoUser.objects.overdue(user)

    tasks = [SlackToDo(task, user).get_block() for task in items]

    text = (
        _("These are the tasks you need to complete:")
        if len(tasks)
        else _("I couldn't find any tasks.")
    )

    Slack().send_message(
        text=text, blocks=[paragraph(text), *tasks], channel=message["user"]
    )


@exception_handler
@app.action(re.compile("(dialog:to_do:)"))
def open_todo_dialog(ack, payload, body):
    ack()
    slack_open_todo_dialog(payload, body)


def slack_open_todo_dialog(payload, body):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    to_do_user = ToDoUser.objects.get(
        id=int(payload["action_id"].split(":")[2]), user=user
    )

    # Avoid race condition. If item is completed, then don't allow to try again
    if to_do_user.to_do.inline_slack_form and to_do_user.completed:

        # Get updated blocks (without completed one, but with text)
        blocks = SlackToDoManager(to_do_user.user).get_blocks(
            [block["block_id"] for block in body["message"]["blocks"]][1:],
            to_do_user.id,
            body["message"]["text"],
        )

        # Remove completed item from message
        Slack().update_message(
            channel=to_do_user.user.slack_channel_id,
            ts=body["container"]["message_ts"],
            blocks=blocks,
        )
        return

    if not to_do_user.to_do.inline_slack_form:
        # Item must be completed on website instead of slack
        if not len(to_do_user.form):
            # User has not filled in form, send warning - cannot complete
            Slack().send_message(
                text=_(
                    "Please complete the form first. Click on 'View details' to "
                    "complete it."
                ),
                channel=body["user"]["id"],
            )
        else:
            # Form is filled in, mark complete
            to_do_user.mark_completed()

            # Get updated blocks (without completed one, but with text)
            blocks = SlackToDoManager(to_do_user.user).get_blocks(
                [block["block_id"] for block in body["message"]["blocks"]][1:],
                to_do_user.id,
                body["message"]["text"],
            )

            # Remove completed item from message
            Slack().update_message(
                channel=to_do_user.user.slack_channel_id,
                ts=body["container"]["message_ts"],
                blocks=blocks,
            )

    else:
        # Show modal to user with to do item
        view = SlackToDo(to_do_user, user).modal_view(
            ids=[block["block_id"] for block in body["message"]["blocks"]],
            text=body["message"]["text"],
            ts=body["container"]["message_ts"],
        )
        Slack().open_modal(trigger_id=body["trigger_id"], view=view)


@exception_handler
@app.event("message", matchers=[no_bot_messages])
def catch_all_message_search_resources(message):
    slack_catch_all_message_search_resources(message)


def slack_catch_all_message_search_resources(message):
    user = get_user(message["user"])
    if user is None:
        return

    items = Resource.objects.search(user, message["text"])
    results = [
        SlackResource(task.resource_new_hire.filter(user=user)[0], user).get_block()
        for task in items
    ]

    text = (
        _("Here is what I found: ")
        if items.count() > 0
        else _("Unfortunately, I couldn't find anything.")
    )
    Slack().send_message(
        blocks=[paragraph(text), *results], text=text, channel=message["user"]
    )


@exception_handler
@app.event("team_join")
def create_new_hire_or_ask_perm(event):
    slack_create_new_hire_or_ask_perm(event)


def slack_create_new_hire_or_ask_perm(event):
    org = Organization.object.get()
    if not org.auto_create_user:
        return

    joined_user = (
        get_user_model()
        .objects.filter(email__iexact=event["user"]["profile"]["email"])
        .first()
    )

    if joined_user is None:

        profile = event["user"]["profile"]
        if "real_name" in profile:
            # This is the fallback option. Not recommended due to names with more than
            # 2 words.
            first_name = profile["real_name"].split(" ")[0]
            if len(profile["real_name"].split(" ")) > 1:
                last_name = profile["real_name"].split(" ")[1]
            else:
                last_name = ""

        if "first_name" in profile:
            first_name = event["user"]["profile"]["first_name"]
        if "last_name" in profile:
            last_name = event["user"]["profile"]["last_name"]

        # First make a generic user (convert to new hire later)
        joined_user = get_user_model().objects.create(
            role=3,
            first_name=first_name,
            last_name=last_name,
            email=event["user"]["profile"]["email"],
            is_active=False,
            timezone=event["user"]["tz"],
            start_day=timezone.now().today(),
        )
        joined_user.set_unusable_password()

    if org.create_new_hire_without_confirm:
        joined_user.role = 0
        joined_user.is_active = True
        joined_user.save()

        # Add default sequences
        joined_user.add_sequences(Sequence.objects.filter(auto_add=True))

    else:
        translation.activate(org.slack_confirm_person.language)

        # needs approval for new hire account
        blocks = [
            paragraph(
                _(
                    "Would you like to put this new hire "
                    "through onboarding?\n*Name:* %(name)s "
                )
                % {"name": joined_user.full_name}
            ),
            actions(
                [
                    button(
                        _("Yeah!"),
                        "primary",
                        str(joined_user.id),
                        "create:newhire:approve",
                    ),
                    button(_("Nope"), "danger", "-1", "create:newhire:deny"),
                ]
            ),
        ]
        Slack().send_message(
            blocks=blocks, channel=org.slack_confirm_person.slack_user_id
        )


@exception_handler
@app.action("create:newhire:approve")
def open_modal_for_selecting_seq_item(ack, body, payload):
    ack()
    slack_open_modal_for_selecting_seq_item(body, payload)


def slack_open_modal_for_selecting_seq_item(body, payload):
    view = {
        "type": "modal",
        "callback_id": "approve:newhire",
        "title": {
            "type": "plain_text",
            "text": _("New hire options"),
        },
        "submit": {"type": "plain_text", "text": _("Create new hire")},
        "blocks": [get_new_hire_approve_sequence_options()],
        "private_metadata": json.dumps(
            {
                "user_id": payload["value"],
                "ts": body["container"]["message_ts"],
            }
        ),
    }
    Slack().open_modal(trigger_id=body["trigger_id"], view=view)


@exception_handler
@app.view("approve:newhire")
def add_sequences_to_new_hire(ack, body, view):
    ack()
    slack_add_sequences_to_new_hire(body, view)


def slack_add_sequences_to_new_hire(body, view):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    private_metadata = json.loads(view["private_metadata"])

    new_hire = get_user_model().objects.get(id=private_metadata["user_id"])
    new_hire.role = 0
    new_hire.save()

    seq_ids = [
        item["value"]
        for item in view["state"]["values"]["seq"]["answers"]["selected_options"]
    ]
    seqs = Sequence.objects.filter(id__in=seq_ids)
    new_hire.add_sequences(seqs)

    org = Organization.object.get()
    Slack().update_message(
        channel=org.slack_confirm_person.slack_channel_id,
        ts=private_metadata["ts"],
        text=_("You approved the request to onboard %(name)s")
        % {"name": new_hire.full_name},
        blocks=[],
    )


@exception_handler
@app.action("create:newhire:deny")
def deny_new_hire(ack, body):
    ack()
    slack_deny_new_hire(body)


def slack_deny_new_hire(body):
    org = Organization.object.get()
    translation.activate(org.language)
    Slack().update_message(
        channel=org.slack_confirm_person.slack_channel_id,
        ts=body["container"]["message_ts"],
        text=_("You denied the request to onboard this person."),
        blocks=[],
    )


@exception_handler
@app.action("show_resource_items")
def show_resource_items(ack, body):
    ack()
    slack_show_all_resources_categories({"user": body["user"]["id"]})


@exception_handler
@app.action(re.compile("(category:)"))
def show_resources_items_in_category(ack, payload, body):
    ack()
    slack_show_resources_items_in_category(payload, body)


def slack_show_resources_items_in_category(payload, body):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    if payload["value"] == "-1":
        resources = ResourceUser.objects.filter(
            user=user, resource__category__isnull=True
        )
    else:
        category = Category.objects.get(id=int(payload["value"]))
        resources = ResourceUser.objects.filter(user=user, resource__category=category)

    blocks = [
        paragraph(_("Here are your options:")),
        *[
            SlackResource(resource_user, user).get_block()
            for resource_user in resources.order_by("resource__name")
        ],
    ]

    Slack().send_message(
        blocks=blocks, text=_("Here are your options:"), channel=body["user"]["id"]
    )


@exception_handler
@app.action(re.compile("(dialog:resource:)"))
def open_resource_dialog(ack, payload, body):
    ack()
    slack_open_resource_dialog(payload, body)


def slack_open_resource_dialog(payload, body):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    resource_user = ResourceUser.objects.get(
        user=user,
        id=int(payload["action_id"].split(":")[2]),
    )
    if resource_user.is_course:
        resource_user.step = 0
        resource_user.save()

    view = SlackResource(resource_user=resource_user, user=user).modal_view(
        resource_user.resource.first_chapter_id
    )

    Slack().open_modal(trigger_id=body["trigger_id"], view=view)


@exception_handler
@app.action("change_resource_page")
def change_resource_page(ack, payload, body):
    ack()
    slack_change_resource_page(payload, body)


def slack_change_resource_page(payload, body):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    # Reuse the menu
    menu = body["view"]["blocks"][0]
    # Get selected chapter from payload
    chapter = Chapter.objects.get(id=payload["selected_option"]["value"])

    Slack().update_modal(
        view_id=body["view"]["id"],
        hash=body["view"]["hash"],
        view={
            "type": "modal",
            "callback_id": body["view"]["callback_id"],
            "title": body["view"]["title"],
            "blocks": [
                menu,
                paragraph(f"*{chapter.name}*"),
                *chapter.to_slack_block(user),
            ],
        },
    )


@exception_handler
@app.action("show_to_do_items")
def show_to_do_items(ack, body):
    ack()
    slack_show_to_do_items(body)


def slack_show_to_do_items(body):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    items = ToDoUser.objects.all_to_do(user)
    tasks = [SlackToDo(task, user).get_block() for task in items]

    text = (
        _("These are the tasks you need to complete:")
        if len(tasks)
        else _("I couldn't find any tasks.")
    )

    Slack().send_message(
        blocks=[paragraph(text), *tasks], text=text, channel=body["user"]["id"]
    )


@exception_handler
@app.view("complete:to_do")
def complete_to_do(ack, body, view):
    ack()
    slack_complete_to_do(body, view)


def slack_complete_to_do(body, view):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    private_meta_data = json.loads(view["private_metadata"])

    # Meta data items
    to_do_ids_from_or_message = private_meta_data["to_do_ids_from_original_message"]
    to_do_id = private_meta_data["to_do_id"]
    text = private_meta_data["text"]
    message_ts = private_meta_data["message_ts"]

    # Get todo item
    to_do_user = ToDoUser.objects.get(id=to_do_id, user=user)

    # Check if there are form items
    for i in to_do_user.to_do.form_items:
        user_data = view["state"]["values"][i["id"]][i["id"]]

        i["answer"] = user_data["value"]

    to_do_user.form = to_do_user.to_do.form_items
    to_do_user.save()

    # Mark complete
    to_do_user.mark_completed()

    # Get updated blocks (without completed one, but with text)
    blocks = SlackToDoManager(to_do_user.user).get_blocks(
        to_do_ids_from_or_message, to_do_id, text
    )

    # Remove completed item from message
    Slack().update_message(
        channel=to_do_user.user.slack_channel_id,
        ts=message_ts,
        blocks=blocks,
    )


@exception_handler
@app.view("dialog:resource")
def next_page_resource(ack, body, view):
    # Course has same meganism
    slack_next_page_resource(ack, body, view)


def slack_next_page_resource(ack, body, view):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    private_meta_data = json.loads(view["private_metadata"])

    # Meta data items
    resource_user = private_meta_data["resource_user"]

    # Get todo item
    resource_user = ResourceUser.objects.get(id=resource_user)

    # Check if there are items
    if (
        bool(view["state"]["values"])
        and "change_resource_page" not in view["state"]["values"]
    ):
        chapter = resource_user.resource.chapters.get(order=resource_user.step)
        data = {}
        for idx, item in enumerate(chapter.content["blocks"]):
            selected_value = view["state"]["values"][f"item-{idx}"][f"item-{idx}"][
                "selected_option"
            ]["value"]
            data[f"item-{idx}"] = selected_value

        course_answers = CourseAnswer.objects.create(chapter=chapter, answers=data)
        resource_user.answers.add(course_answers)

    next_chapter = resource_user.add_step()
    if next_chapter is None:
        ack({"response_action": "clear"})
        return

    private_meta_data["current_chapter"] = next_chapter.id

    # Get updated blocks (without completed one, but with text)
    view = {
        "type": "modal",
        "callback_id": view["callback_id"],
        "title": view["title"],
        "private_metadata": json.dumps(private_meta_data),
        "blocks": [
            paragraph(f"*{next_chapter.name}*"),
            *next_chapter.to_slack_block(user),
        ],
    }

    if resource_user.is_course:
        if resource_user.step + 1 == resource_user.amount_chapters_in_course:
            view["submit"] = {"type": "plain_text", "text": _("Complete")}
        else:
            view["submit"] = {"type": "plain_text", "text": _("Next")}

    ack({"response_action": "update", "view": view})
    # This is only used for testing - should be removed and fixed
    if settings.FAKE_SLACK_API:
        Slack().update_modal(
            view_id=body["view"]["id"], hash=body["view"]["hash"], view=view
        )


@exception_handler
@app.action("admin_task:complete")
def complete_admin_task(ack, body, payload):
    ack()
    slack_complete_admin_task(body, payload)


def slack_complete_admin_task(body, payload):
    user = get_user(body["user"]["id"])
    if user is None:
        return

    admin_task = AdminTask.objects.get(id=payload["value"])
    admin_task.completed = True
    admin_task.save()
    Slack().update_message(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"],
        text=_("Thanks! This has been marked as completed."),
        blocks=[],
    )


@exception_handler
@app.action("dialog:welcome")
def show_welcome_dialog(ack, body, payload):
    ack()
    slack_show_welcome_dialog(body, payload)


def slack_show_welcome_dialog(body, payload):
    org = Organization.object.get()
    translation.activate(org.language)

    user = get_user(body["user"]["id"])
    if user is None:
        return

    view = {
        "type": "modal",
        "callback_id": "save:welcome",
        "title": {
            "type": "plain_text",
            "text": _("Welcome this new hire!"),
        },
        "submit": {"type": "plain_text", "text": _("Submit")},
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
                    "text": _("What would you like to say to our new hire?"),
                },
            }
        ],
        "private_metadata": json.dumps({"user_id": payload["value"]}),
    }
    if len(view["title"]["text"]) > 24:
        view["title"]["text"] = view["title"]["text"][:21] + "..."
    Slack().open_modal(trigger_id=body["trigger_id"], view=view)


@exception_handler
@app.view("save:welcome")
def save_welcome_message(ack, body, view):
    ack()
    slack_save_welcome_message(body, view)


def slack_save_welcome_message(body, view):
    org = Organization.object.get()

    user = get_user(body["user"]["id"])
    if user is None:
        return

    private_metadata = json.loads(view["private_metadata"])

    new_hire = get_user_model().objects.get(id=private_metadata["user_id"])

    message_to_new_hire = view["state"]["values"]["input"]["message"]["value"]
    NewHireWelcomeMessage.objects.update_or_create(
        colleague=user,
        new_hire=new_hire,
        defaults={"message": message_to_new_hire},
    )

    send_to = (
        org.slack_default_channel.name
        if org.slack_default_channel is not None
        else "general"
    )
    Slack().send_ephemeral_message(
        channel="#" + send_to,
        user=user.slack_user_id,
        text=_('Message has been saved! Your message: "') + message_to_new_hire + '"',
    )
