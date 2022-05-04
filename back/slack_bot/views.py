import re
import json
import urllib.parse

from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework.response import Response

from admin.admin_tasks.models import AdminTask
from admin.integrations.models import Integration
from admin.resources.models import Category, Chapter, CourseAnswer
from admin.sequences.models import Sequence

from organization.models import Organization
from users.models import NewHireWelcomeMessage, ResourceUser, ToDoUser
from admin.resources.models import Resource
from admin.to_do.models import ToDo

from .slack_join import SlackJoin
from .slack_misc import get_new_hire_approve_sequence_options, welcome_new_hire
from .slack_resource import SlackResource
from .slack_to_do import SlackToDo, SlackToDoManager
from .utils import Slack, paragraph

from slack_bolt import App as SlackBoltApp
import logging
logger = logging.getLogger(__name__)
from sentry_sdk import capture_exception


from .slack_resource import SlackResource, SlackResourceCategory

if settings.SLACK_USE_SOCKET:
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    app = SlackBoltApp(token=settings.SLACK_BOT_TOKEN, raise_error_for_unhandled_request=False, logger=logger)

    slack_handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
    slack_handler.connect()
else:
    integration = Integration.objects.filter(integration=0).first()
    app = SlackBoltApp(token=integration.token, signing_secret=integration.signing_secret)


def exception_handler(func):
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            capture_exception(e)
    return inner_function


def no_bot_messages(message) -> bool:
    return message.get("subtype") != "bot_message" and ("message" not in message or "bot_id" not in message.get("message"))


@exception_handler
@app.error
def custom_error_handler(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")


@exception_handler
@app.message(re.compile("(help)"), matchers=[no_bot_messages])
def show_help(message, say):
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

    say("".join(messages))


def get_user(slack_user_id, say):
    users = get_user_model().objects.filter(slack_user_id=slack_user_id)
    if users.exists():
        return users.first()
    else:
        say(
                _(
                    "You don't seem to be setup yet. Please ask your supervisor for"
                    " access."
                )
            )


@exception_handler
@app.message(re.compile("(resource)"), matchers=[no_bot_messages])
def show_all_resources_categories(message, say):
    user = get_user(message["user"], say)
    if user is None:
        return
    blocks = [paragraph(_("Select a category:")), *SlackResourceCategory(user=user).category_buttons()]
    say(blocks=blocks, text=_("Select a category:"))


@exception_handler
@app.message(re.compile("(to do|todo|todos)"), matchers=[no_bot_messages])
def show_to_do_items_based_on_message(message, say):
    user = get_user(message["user"], say)
    if user is None:
        return

    items = ToDoUser.objects.all_to_do(user)
    if _("today") in message["text"]:
        items = ToDoUser.objects.due_today(user)
    if _("overdue") in message["text"]:
        items = ToDoUser.objects.overdue(user)

    tasks = [SlackToDo(task.to_do, user).to_do_block() for task in items]

    text = (
        _("These are the tasks you need to complete:")
        if len(tasks)
        else _("I couldn't find any tasks.")
    )

    say(blocks=[paragraph(text), *tasks], text=text)


@exception_handler
@app.action(re.compile("(dialog:to_do:)"))
def open_todo_dialog(ack, payload, body, say, client):
    ack()
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    to_do_user = ToDoUser.objects.get(
        user=user,
        to_do=ToDo.objects.get(id=int(payload["action_id"].split(":")[2])),
    )
    if not to_do_user.to_do.inline_slack_form:
        # Item must be completed on website instead of slack
        if not len(to_do_user.form):
            say(
                    _(
                        "Please complete the form first. Click on 'View details' to "
                        "complete it."
                )
            )
        else:
            to_do_user.mark_completed()

            # Get updated blocks (without completed one, but with text)
            blocks = SlackToDoManager(to_do_user.user).get_blocks(
                [block["block_id"] for block in body["message"]["blocks"]][1:], to_do_user.to_do.id, body["message"]["blocks"]["text"]["text"]
            )

            # Remove completed item from message
            client.chat_update(
                channel=to_do_user.user.slack_channel_id,
                ts=body["containers"]["message_ts"],
                blocks=blocks,
            )

    else:
        view = SlackToDo(
            to_do_user.to_do, user
        ).modal_view(
            ids=[block["block_id"] for block in body["message"]["blocks"]],
            text=body["message"]["text"],
            ts=body["container"]["message_ts"],
        )
        client.views_open(
            trigger_id=body["trigger_id"],
            view=view
        )


@exception_handler
@app.event("message", matchers=[no_bot_messages])
def catch_all_message_search_resources(message, say):
    user = get_user(message["user"], say)
    if user is None:
        return

    items = Resource.objects.search(user, message["text"])
    results = [SlackResource(task.resource_new_hire.all()[0], user).get_block() for task in items]

    text = (
        _("Here is what I found: ")
        if items.count() > 0
        else _("Unfortunately, I couldn't find anything.")
    )
    say(blocks=[paragraph(text), *results], text=text)


@exception_handler
@app.event("team_join")
def create_new_hire_or_ask_perm(event, say):
    print("JOINED TEAM")
    SlackJoin(event).create_new_hire_or_ask_permission()


@exception_handler
@app.action("create:newhire:approve")
def open_modal_for_selecting_seq_item(ack, body, payload, say, client):
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
    client.views_open(
        trigger_id=body["trigger_id"],
        view=view
    )


@exception_handler
@app.view("approve:newhire")
def add_sequences_to_new_hire(ack, say, body, client, view):

    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    private_metadata = json.loads(view["private_metadata"])

    new_hire = get_user_model().objects.get(id=private_metadata["user_id"])
    new_hire.role = 0
    new_hire.save()

    seq_ids = [item["value"] for item in body["view"]["state"]["values"]["seq"]["answers"]["selected_option"]["value"]]
    seqs = Sequence.objects.filter(id__in=seq_ids)
    new_hire.add_sequences(seqs)

    client.chat_update(
        channel=body["container"]["channel_id"],
        ts=private_metadata["ts"],
        text="<@{admin_id}> approved the request for onboarding <@{new_hire_id}>",
        blocks=[]
    )
    ack()



@exception_handler
@app.action("create:newhire:deny")
def deny_new_hire(ack, body, client):
    client.chat_update(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"],
        text="<@{admin_id}> denied the request for onboarding <@{new_hire_id}>",
        blocks=[]
    )

    ack()

@exception_handler
@app.action("show_resource_items")
def show_resource_items(ack, body, say):
    ack()
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    blocks = [paragraph(_("Select a category:")), *SlackResourceCategory(user=user).category_buttons()]
    say(blocks=blocks, text=_("Select a category:"))


@exception_handler
@app.action(re.compile("(category:)"))
def show_resources_items_in_category(ack, payload, body, say):
    ack()

    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    if payload["value"] == "-1":
        resources = ResourceUser.objects.filter(
            user=user, resource__category__isnull=True
        )
    else:
        category = Category.objects.get(
            id=int(payload["value"])
        )
        resources = ResourceUser.objects.filter(
            user=user, resource__category=category
        )

    blocks = [paragraph(_("Here are your options:")), *[SlackResource(resource_user, user).get_block() for resource_user in resources]]

    say(blocks=blocks, text=_("Here are your options:"))


@exception_handler
@app.action(re.compile("(dialog:resource:)"))
def open_resource_dialog(ack, payload, body, say, client):
    ack()
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    resource_user = ResourceUser.objects.get(
        user=user,
        id=int(payload["action_id"].split(":")[2]),
    )
    resource_user.step = 0
    resource_user.save()

    view = SlackResource(
        resource_user=resource_user, user=user
    ).modal_view(resource_user.resource.first_chapter_id)

    client.views_open(
        trigger_id=body["trigger_id"],
        view=view
    )

@exception_handler
@app.action("change_resource_page")
def change_resource_page(ack, payload, body, say, client):
    ack()
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    # Reuse the menu
    menu = body["view"]["blocks"][0]
    # Get selected chapter from payload
    chapter = Chapter.objects.get(id=payload["selected_option"]["value"])

    client.views_update(
        view_id = body["view"]["id"],
        hash = body["view"]["hash"],
        view = {
            "type": "modal",
            "callback_id": body["view"]["callback_id"],
            "title": body["view"]["title"],
            "blocks": [menu, paragraph(f"*{chapter.name}*"), *chapter.to_slack_block(user)]
        }
    )


@exception_handler
@app.action("show_to_do_items")
def show_to_do_items(ack, body, say):
    ack()

    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    items = ToDoUser.objects.all_to_do(user)
    tasks = [SlackToDo(task.to_do, user).to_do_block() for task in items]

    text = (
        _("These are the tasks you need to complete:")
        if len(tasks)
        else _("I couldn't find any tasks.")
    )

    say(blocks=[paragraph(text), *tasks], text=text)


@exception_handler
@app.view("complete:to_do")
def complete_to_do(ack, say, body, client, view):
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    private_meta_data = json.loads(view["private_metadata"])

    # Meta data items
    to_do_ids_from_or_message = private_meta_data["to_do_ids_from_original_message"]
    to_do_id = private_meta_data["to_do_id"]
    text = private_meta_data["text"]
    message_ts = private_meta_data["message_ts"]

    # Get todo item
    to_do = ToDo.objects.get(id=to_do_id)
    to_do_user = ToDoUser.objects.get(to_do=to_do, user=user)

    # Check if there are form items
    print(to_do_user.to_do.form_items)
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
    client.chat_update(
        channel=to_do_user.user.slack_channel_id,
        ts=message_ts,
        blocks=blocks,
    )

    ack()


@exception_handler
@app.view("dialog:resource")
def next_page_resource(ack, say, body, client, view):
    # Course has same meganism
    print("next page")
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    private_meta_data = json.loads(view["private_metadata"])

    # Meta data items
    # current_chapter = private_meta_data["current_chapter"]
    resource_user = private_meta_data["resource_user"]

    # Get todo item
    resource_user = ResourceUser.objects.get(id=resource_user)

    # Check if there are items
    if bool(body["view"]["state"]["values"]):
        chapter = resource_user.resource.chapters.get(order=resource_user.step)
        data = {}
        for idx, item in enumerate(chapter.content["blocks"]):
            selected_value = body["view"]["state"]["values"][f"item-{idx}"][f"item-{idx}"]["selected_option"]["value"]
            data[f"item-{idx}"] = selected_value

        course_answers = CourseAnswer.objects.create(
            chapter=chapter, answers=data
        )
        resource_user.answers.add(course_answers)

    next_chapter = resource_user.add_step()
    print(next_chapter)
    if next_chapter is None:
        ack({"response_action": "clear"})
        return
    # Get updated blocks (without completed one, but with text)
    view = {
        "type": "modal",
        "callback_id": body["view"]["callback_id"],
        "title": body["view"]["title"],
        "private_metadata": view["private_metadata"],
        "blocks": [paragraph(f"*{next_chapter.name}*"), *next_chapter.to_slack_block(user)]
    }

    if resource_user.is_course:
        if resource_user.step + 1 == resource_user.amount_chapters_in_course:
            view["submit"] = {"type": "plain_text", "text": _("Complete") }
        else:
            view["submit"] = {"type": "plain_text", "text": _("Next") }


    ack({"response_action": "update", "view": view })


@exception_handler
@app.action("admin_task:complete")
def complete_admin_task(ack, say, body, payload):
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    admin_task = AdminTask.objects.get(
        id=payload["action_id"]
    )
    admin_task.completed = True
    admin_task.save()

    ack()


@exception_handler
@app.action("dialog:welcome")
def show_welcome_dialog(ack, say, body, payload, client):
    user = get_user(body["user"]["id"], say)
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
        "blocks": [welcome_new_hire],
        "private_metadata": json.dumps(
             {
                 "user_id": payload["value"]
             }
         ),
    }
    client.views_open(
        trigger_id=body["trigger_id"],
        view=view
    )

    ack()


@exception_handler
@app.view("welcome")
def save_welcome_message(ack, say, body, payload, client, view):
    user = get_user(body["user"]["id"], say)
    if user is None:
        return

    private_metadata = json.loads(view["private_metadata"])

    new_hire = get_user_model().objects.get(id=private_metadata["user_id"])

    message_to_new_hire = body["view"]["state"]["values"]["input"]["message"]["value"]
    NewHireWelcomeMessage.objects.update_or_create(
        colleague=user,
        new_hire=new_hire,
        defaults={"message": message_to_new_hire},
    )

    client.chat_postEphemeral(
        channel=payload["channel"],
        user=user,
        text=_('Message has been saved! Your message: "') + message_to_new_hire + '"'
    )

    ack()
