import json
import hmac
import hashlib
import urllib.parse

from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework.response import Response

from admin.admin_tasks.models import AdminTask
from admin.integrations.models import Integration
from admin.resources.models import Category, Chapter
from admin.sequences.models import Sequence

# from fuzzywuzzy import process
from organization.models import Organization
from users.models import NewHireWelcomeMessage, ResourceUser, ToDoUser

from .slack_block_actions import SlackBlockAction
from .slack_incoming_message import SlackIncomingMessage
from .slack_join import SlackJoin
from .slack_misc import get_new_hire_approve_sequence_options, welcome_new_hire
from .slack_modal import SlackModal
from .slack_resource import SlackResource
from .slack_to_do import SlackToDo, SlackToDoManager
from .utils import Slack

import logging
logger = logging.getLogger(__name__)


def is_valid_slack_request(request):
    slack_integration = Integration.objects.filter(integration=0).first()
    if slack_integration is None:
        return False

    try:
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        sig_basestring = 'v0:' + timestamp + ':' + request.body.decode('utf-8')
        our_signature = 'v0=' + hmac.new(
            slack_integration.signing_secret.encode(),
            msg=sig_basestring.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        slack_signature = request.headers.get('X-Slack-Signature', '')

        if hmac.compare_digest(our_signature, slack_signature):
            return True
    except:
        return False
    return False


@method_decorator(csrf_exempt, name='dispatch')
class BotView(View):
    """
    Slack events endpoint. All messages and events come in here. (except for
    interactions with dialogs and buttons).
    """

    def post(self, request):
        # verify Slack request endpoint
        if not is_valid_slack_request(request):
            return HttpResponse()

        logger.error(request.body)
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        logger.error(data)

        print(data)
        if "type" in data and data["type"] == "url_verification":
            return HttpResponse(data["challenge"])

        # strictly allow only messages or team_join requests
        if (
            "event" not in data
            or "bot_id" in data["event"]
            or "subtype" in data["event"]
            or (
                data["event"]["type"] != "message"
                and data["event"]["type"] != "team_join"
            )
        ):
            return HttpResponse("ok")

        # avoid second requests
        if "X-Slack-Retry-Num" in request.META:
            return HttpResponse("ok")

        org = Organization.object.get()

        # whenever a person joins Slack
        if data["event"]["type"] == "team_join":
            # check if setting has been enabled to auto create accounts from slack
            if org.auto_create_user:
                SlackJoin(data["event"]).create_new_hire_or_ask_permission()

        # when someone sends a message to the bot in a DM
        if data["event"]["type"] == "message":
            print("message event")
            slack_im = SlackIncomingMessage(data)
            print(slack_im)

            # check if user actually has a new hire/admin/colleague account
            if not slack_im.user_exists():
                blocks = slack_im.reply_request_access_supervisor()

            elif slack_im.is_request_for_help():
                blocks = slack_im.reply_with_help_options()

            elif slack_im.is_request_for_to_do():
                blocks = slack_im.reply_with_to_do_items()

            elif slack_im.is_request_for_resources():
                blocks = slack_im.reply_with_resource_categories()

            else:
                blocks = slack_im.reply_with_search_results()

            Slack().send_message(blocks, data["event"]["user"])

        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class CallbackView(View):
    """
    Button interactions come back here
    """

    def post(self, request):
        # very hacky, but this is a Django/DRF issue
        if not is_valid_slack_request(request):
            return HttpResponse()

        body_json = urllib.parse.parse_qs(request.body.decode('utf-8'))
        response = json.loads(body_json["payload"][0])

        print(response)
        # respond to click on any of the blocks
        if response["type"] == "block_actions":
            print("IS BLOCK ACTION")

            slack_block_action = SlackBlockAction(response)

            # drop if user does not exist
            if not slack_block_action.get_user():
                print("USER DOES NOT EXIST")
                return HttpResponse()

            if slack_block_action.is_change_resource_page():
                print("IS CHANGE PAGE")
                slack_modal = SlackModal(response)
                resource_user_id = slack_modal.get_private_metadata()["resource_user"]
                chapter = int(
                    slack_block_action.get_action()["selected_option"]["value"]
                )

                view = SlackResource(
                    resource_user=ResourceUser.objects.get(id=resource_user_id),
                    user=slack_block_action.user,
                ).modal_view(chapter)
                Slack().update_modal(view_id=response["view"]["id"], view=view)
                return HttpResponse()

            # Someone completed an admin task (hit the "done" button)
            if slack_block_action.is_type("admin_task"):
                admin_task = AdminTask.objects.get(
                    id=slack_block_action.action_array()[2]
                )
                admin_task.completed = True
                admin_task.save()
                return HttpResponse()

            # New hire clicked on "to do" button on first message
            if slack_block_action.is_type("to_do") and not slack_block_action.is_type("dialog:to_do"):
                print("HIT TODO BUTTON")
                blocks = slack_block_action.reply_to_do_items()
                Slack().send_message(blocks, slack_block_action.get_channel())

            # New hire clicked on "resource" button on first message
            if slack_block_action.is_type("resources"):
                blocks = slack_block_action.reply_with_resource_categories()
                Slack().send_message(blocks, slack_block_action.get_channel())

            # Admin clicked on the deny/approve "approve new hire" button
            if slack_block_action.is_type("create:newhire"):

                if slack_block_action.is_type("deny"):
                    # delete message when it's denied to not clutter things up
                    Slack().delete_message(
                        channel=slack_block_action.get_channel(),
                        ts=slack_block_action.get_timestamp_message(),
                    )

                if slack_block_action.is_type("approve"):
                    # approved new hire: show modal with sequence choices
                    view = SlackModal().create_view(
                        title=_("New hire options"),
                        blocks=[get_new_hire_approve_sequence_options()],
                        callback="approve:newhire",
                        private_metadata=json.dumps(
                            {
                                "user_id": slack_block_action.action_array()[3],
                                "ts": slack_block_action.get_action()["action_ts"],
                            }
                        ),
                        submit_name=_("Create new hire"),
                    )
                    Slack().open_modal(
                        trigger_id=slack_block_action.get_trigger_id(), view=view
                    )

                return HttpResponse()

            # User clicked button to open a modal
            if slack_block_action.is_type("dialog"):

                # To do modal for the new hire to complete
                if slack_block_action.is_type("to_do"):

                    # get to do item
                    to_do_user = ToDoUser.objects.get(
                        id=slack_block_action.action_array()[2]
                    )

                    view = SlackToDo(
                        to_do_user.to_do, slack_block_action.user
                    ).create_modal_view(
                        ids=slack_block_action.get_block_ids(),
                        text=slack_block_action.get_blocks()[0]["text"],
                        ts=slack_block_action.get_timestamp_message(),
                    )
                    Slack().open_modal(
                        trigger_id=slack_block_action.get_trigger_id(), view=view
                    )
                    return HttpResponse()

                # open modal to type personal welcome message for new hire
                if slack_block_action.is_type("welcome"):
                    view = SlackModal().create_view(
                        title=_("Welcome this new hire!"),
                        blocks=[welcome_new_hire],
                        callback="welcome",
                        # private metadata is the new hire id
                        private_metadata=slack_block_action.action_array()[2],
                    )
                    Slack().open_modal(
                        trigger_id=slack_block_action.get_trigger_id(), view=view
                    )
                    return HttpResponse()

                # resource/course was clicked: show first chapter
                if slack_block_action.is_type("resource"):
                    resource_user = ResourceUser.objects.get(
                        user=slack_block_action.user,
                        id=int(slack_block_action.action_array()[2]),
                    )
                    view = SlackResource(
                        resource_user=resource_user, user=slack_block_action.user
                    ).modal_view(-1)
                    Slack().open_modal(
                        trigger_id=slack_block_action.get_trigger_id(), view=view
                    )
                    return HttpResponse()

            # User clicked complete button with external form
            if slack_block_action.is_type("to_do:external"):
                to_do_user = ToDoUser.objects.get(
                    id=slack_block_action.action_array()[2]
                )
                # Check if form has actually been filled
                if len(to_do_user.form) == 0:
                    blocks = SlackToDo(
                        to_do_user, slack_block_action.user
                    ).not_completed_message()
                    Slack().send_message(
                        blocks=blocks, channel=slack_block_action.get_channel()
                    )
                    return HttpResponse()

                # Mark item completed and check conditions for triggers
                to_do_user.mark_completed()

                # delete current item and reload blocks
                blocks = SlackToDoManager(slack_block_action.user).get_blocks(
                    slack_block_action.get_block_ids(), to_do_user.id
                )
                Slack().update_message(
                    blocks=blocks,
                    channel=slack_block_action.get_channel(),
                    timestamp=slack_block_action.get_timestamp_message(),
                )
                return HttpResponse()

            # show resources based on category
            if slack_block_action.is_type("category"):
                # Show resources that don't have a category
                if slack_block_action.action_array()[1] == "-1":
                    resource_user = ResourceUser.objects.filter(
                        user=slack_block_action.user, resource__category__isnull=True
                    )
                else:
                    category = Category.objects.get(
                        id=int(slack_block_action.action_array()[1])
                    )
                    resource_user = ResourceUser.objects.filter(
                        user=slack_block_action.user, resource__category=category
                    )

                blocks = SlackResource(
                    resource_user, slack_block_action.user
                ).get_block()

                Slack().send_message(blocks, slack_block_action.get_channel())
                return HttpResponse()

        # respond to a dialog completion
        print(response["type"])
        if response["type"] == "view_submission":
            slack_modal = SlackModal(response)

            # save welcome message from colleague to new hire
            if slack_modal.is_type("welcome"):
                new_hire_id = int(slack_modal.get_private_metadata())
                new_hire = get_user_model().objects.get(id=new_hire_id)

                message = slack_modal.get_filled_in_values()["input"]["message"][
                    "value"
                ]

                NewHireWelcomeMessage.objects.update_or_create(
                    colleague=slack_modal.user,
                    new_hire=new_hire,
                    defaults={"message": message},
                )

                return HttpResponse()

            # save to do and optionally the form that got submitted with it
            if slack_modal.is_type("complete:to_do"):

                print("finish TODO")
                to_do_ids_from_or_message = slack_modal.get_private_metadata()[
                    "to_do_ids_from_original_message"
                ]
                to_do_id = slack_modal.get_private_metadata()["to_do_id"]
                text = slack_modal.get_private_metadata()["text"]
                message_ts = slack_modal.get_private_metadata()["message_ts"]

                to_do_user = ToDoUser.objects.get(id=to_do_id)

                # Check if there are form items
                for i in to_do_user.to_do.form_items:
                    user_data = slack_modal.get_filled_in_values()[i["id"]][i["id"]]

                    i["answer"] = user_data["value"]

                to_do_user.form = to_do_user.to_do.form_items
                to_do_user.save()

                to_do_user.mark_completed()

                # Remove the completed block and show old ones
                blocks = SlackToDoManager(to_do_user.user).get_blocks(
                    to_do_ids_from_or_message, to_do_id, text
                )
                Slack().update_message(
                    blocks=blocks,
                    channel=slack_modal.get_channel(),
                    timestamp=message_ts,
                )

                return HttpResponse()

            if slack_modal.is_type("dialog:resource"):

                resource_user_id = slack_modal.get_private_metadata()["resource_user"]
                chapter_id = slack_modal.get_private_metadata()["current_chapter"]

                resource_user = ResourceUser.objects.get(
                    user=slack_modal.user, id=resource_user_id
                )
                chapter = Chapter.objects.get(id=chapter_id)

                # saving form
                # TODO
                if (
                    "state" in response["view"]
                    and "values" in response["view"]["state"]
                ):
                    # form = ContentSerializer(chapter.content, many=True).data
                    # answers = []
                    # for i in form:
                    #     answers.append(
                    #         response["view"]["state"]["values"][str(i["id"])][
                    #             str(i["id"])
                    #         ]["selected_option"]["value"]
                    #     )
                    # course_answer, cre = book_user.answers.get_or_create(
                    #     chapter=chapter, defaults={"answers": answers}
                    # )
                    # if not cre:
                    #     course_answer.answers = answers
                    # else:
                    #     book_user.answers.add(course_answer)
                    print(response["view"]["state"]["values"])

                view = SlackResource(
                    resource_user=resource_user, user=slack_modal.user
                ).modal_view(chapter.id)
                Slack().open_modal(
                    trigger_id=response["trigger_id"], view=view
                )
                return HttpResponse()

            if slack_modal.is_type("approve:newhire"):

                user_id = slack_modal.get_private_metadata()["user_id"]
                timestamp = slack_modal.get_private_metadata()["timestamp"]

                new_hire = get_user_model().objects.get(id=user_id)
                new_hire.role = 0
                new_hire.save()

                seq_ids = [
                    seq["value"]
                    for seq in slack_modal.get_filled_in_values()["seq"]["answers"][
                        "selected_options"
                    ]
                ]
                seqs = Sequence.objects.filter(id__in=seq_ids)
                new_hire.add_sequences(seqs)

                # delete message when it's approved to not clutter things up
                Slack().delete_message(channel=slack_modal.get_channel(), ts=timestamp)

        return HttpResponse()
