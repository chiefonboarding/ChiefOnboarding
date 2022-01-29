import json
import urllib
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from admin.admin_tasks.models import AdminTask
from admin.integrations.models import AccessToken
from users.models import NewHireWelcomeMessage, ResourceUser
from admin.resources.models import Category, Chapter
from misc.serializers import ContentSerializer
from admin.sequences.models import Sequence

# from fuzzywuzzy import process
from organization.models import Organization
from users.models import NewHireWelcomeMessage, ResourceUser, ToDoUser, User

from .slack import Slack


class BotView(APIView):
    """
    API endpoint that allows notes to be deleted.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        # verify Slack request endpoint
        if "type" in request.data and request.data["type"] == "url_verification":
            return Response(request.data["challenge"])

        # verify Slack request endpoint
        if (
            "token" not in request.data
            or not AccessToken.objects.filter(
                verification_token=request.data["token"]
            ).exists()
        ):
            return Response()

        # avoid bot requests
        if (
            "bot_id" in request.data["event"]
            or not "event" in request.data
            or "subtype" in request.data["event"]
            or (
                request.data["event"]["type"] != "message"
                and request.data["event"]["type"] != "team_join"
            )
        ):
            return Response("ok")

        # avoid second requests
        if "X-Slack-Retry-Num" in request.META:
            return Response("ok")

        # whenever a person joins Slack
        if request.data["event"]["type"] == "team_join":
            org = Organization.object.get()
            s = Slack()
            user = s.find_user_by_id(request.data["event"]["user"]["id"])
            if (
                org.auto_create_user
                and not User.objects.filter(email=user["profile"]["email"]).exists()
            ):
                if len(user["profile"]["real_name"].split(" ")) > 1:
                    first_name = user["profile"]["real_name"].split(" ")[0]
                    last_name = user["profile"]["real_name"].split(" ")[1]
                else:
                    first_name = user["profile"]["real_name"]
                    last_name = ""

                user = User.objects._create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=user["profile"]["email"],
                    password=None,
                    role=3,
                    timezone=user["tz"],
                    start_day=datetime.now(),
                )
                if org.create_new_hire_without_confirm:
                    user.role = 0
                    user.save()
                    # adding default sequences
                    for i in Sequence.objects.filter(auto_add=True):
                        i.assign_to_user(user)

                else:
                    # needs approval for new hire account
                    s = Slack()
                    s.set_user(org.slack_confirm_person)
                    blocks = s.format_account_approval_approval(
                        request.data["event"]["user"], user.id
                    )
                    s.send_message(blocks=blocks)
            return Response("ok")

        s = Slack(request.data)
        if not s.has_account():
            s.send_message(
                text="You don't seem to be setup yet. Please ask your supervisor for access."
            )
            return Response()

        if s.text == "hello":
            s.send_message(text="hi")
        elif "to do" in s.text:
            tasks = ToDoUser.objects.filter(user=s.user_obj, completed=False)
            if "today" in s.text:
                tasks = tasks.filter(to_do__due_on_day=s.user_obj.workday())
            if "overdue" in s.text:
                tasks = tasks.filter(to_do__due_on_day__lt=s.user_obj.workday())
            text = (
                _("These are the tasks you need to complete:")
                if tasks.exists()
                else _("I couldn't find any tasks.")
            )
            blocks = s.format_to_do_block(pre_message=text, items=tasks)
            s.send_message(blocks=blocks)

        elif "resources" in s.text:
            # show categories
            categories = []
            if s.user_obj.resources.filter(category__isnull=True).exists():
                categories.append({"name": "No category", "id": -1})
            for i in s.user_obj.resources.all():
                if i.category is not None and categories.index(i.category.name) != -1:
                    categories.append(i.category)
            blocks = s.create_buttons(categories=categories)
            s.send_message(blocks=blocks)

        elif "help" in s.text:
            s.help()

        else:
            # get all stuff in a searchable array
            searchable_array = []
            tasks = s.user_obj.resources.all()

            for i in tasks:
                searchable_array.append(i.name)

            resources = []
            t = ""
            for i in text:
                t += i + " "
            # output = process.extract(t.strip(), searchable_array, limit=7)
            # for o in output:
            #     if o[1] > 50:
            #         resources.append(ResourceUser.objects.filter(user=s.user_obj, resource__name=o[0]).first())
            blocks = []
            text = (
                _("Here is what I found: ")
                if len(resources) > 0
                else _("Unfortunately, I couldn't find anything.")
            )
            blocks.extend(s.format_resource_block(resources, pre_message=text))
            s.send_message(blocks=blocks)

        return Response("ok")


class CallbackView(APIView):
    """
    API endpoint that allows notes to be deleted.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        # very hacky, but this is a Django/DRF issue
        response = "{" + urllib.parse.unquote(request.body.decode("utf-8")[11:-3]) + "}"
        response = json.loads(response.replace("+", " "))

        # verify Slack request endpoint
        if (
            "token" not in response
            or not AccessToken.objects.filter(
                verification_token=response["token"]
            ).exists()
        ):
            return Response()

        s = Slack(response)
        s.set_user(get_user_model().objects.get(slack_user_id=response["user"]["id"]))

        # respond to click on any of the blocks
        if response["type"] == "block_actions":
            if response["actions"][0]["block_id"] == "change_page":
                value = int(response["actions"][0]["selected_option"]["value"])
                view_id = response["view"]["id"]
                view = s.create_updated_view(value, response["view"], True)

                s.client.views_update(view=view, view_id=view_id)
                return Response()

            value = response["actions"][0]["value"]

            if "admin_task" in value:
                admin_task = AdminTask.objects.get(id=value.split(":")[2])
                admin_task.completed = True
                admin_task.save()
                return Response()

            if "to_do" == value:
                tasks = ToDoUser.objects.filter(user=s.user_obj, completed=False)
                if tasks.exists():
                    blocks = s.format_to_do_block(
                        pre_message=_("These are the tasks you need to complete:"),
                        items=tasks,
                    )
                    s.send_message(blocks=blocks)
                return Response()

            if "resource" == value:
                tasks = ResourceUser.objects.filter(user=s.user_obj)
                if tasks.exists():
                    blocks = s.format_resource_block(items=tasks)
                    s.send_message(blocks=blocks)
                return Response()

            # responding to approving new hires directly from Slack (people that joined Slack)
            if "create:newhire" in value:
                if "deny" in value:
                    # delete message when it's denied to not clutter things up
                    s.client.chat_delete(
                        channel=s.channel, ts=response["message"]["ts"]
                    )
                if "approve" in value:
                    options = []
                    for i in Sequence.objects.all()[:100]:
                        options.append(
                            {
                                "text": {"type": "plain_text", "text": i.name},
                                "value": str(i.id),
                            }
                        )
                    s.open_modal(
                        trigger_id=response["trigger_id"],
                        callback="approve:newhire" + ":" + s.container["message_ts"],
                        title="New hire options",
                        blocks=[
                            {
                                "type": "input",
                                "block_id": "seq",
                                "label": {
                                    "type": "plain_text",
                                    "text": "Select sequences",
                                },
                                "element": {
                                    "type": "multi_static_select",
                                    "placeholder": {
                                        "type": "plain_text",
                                        "text": "Select sequences",
                                    },
                                    "options": options,
                                    "action_id": "answers",
                                },
                            }
                        ],
                        private_metadata=value.split(":")[3],
                        submit_name="Create new hire",
                    )
                return Response()

            # open modal
            if "dialog" in value:

                # to do modal
                if "to_do" in value:
                    to_do_user = ToDoUser.objects.get(id=value.split(":")[2])
                    blocks = []
                    for i in to_do_user.to_do.content.all():
                        blocks.append(i.to_slack_block(s.user_obj))
                    blocks.extend(to_do_user.to_do.get_slack_form())
                    private_metadata = [
                        x["block_id"] for x in response["message"]["blocks"]
                    ]
                    private_metadata[0] = response["message"]["blocks"][0]["text"][
                        "text"
                    ]
                    s.open_modal(
                        response["trigger_id"],
                        to_do_user.to_do.name,
                        blocks,
                        callback="complete:to_do:"
                        + value.split(":")[2]
                        + ":"
                        + s.container["message_ts"],
                        private_metadata=str(private_metadata),
                        submit_name=None,
                    )
                    return Response()

                # welcome message for new hire
                if "welcome" in value:
                    s.open_modal(
                        response["trigger_id"],
                        "Leave a kind message!",
                        [
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
                        callback="welcome:" + value.split(":")[2],
                        private_metadata="",
                        submit_name=None,
                    )
                    return Response()

                # show first resource
                if "resource" in value or "course" in value:
                    book_user = ResourceUser.objects.get(
                        user=s.user_obj, id=int(value.split(":")[2])
                    )
                    options = []
                    blocks = []
                    type = "course"
                    if "resource" in value or book_user.completed_course:
                        type = "resource"
                        for i in book_user.resource.chapters.exclude(type=2):
                            options.append(i.slack_menu_item())
                        blocks.append(
                            {
                                "type": "actions",
                                "block_id": "change_page",
                                "elements": [
                                    {
                                        "type": "static_select",
                                        "placeholder": {
                                            "type": "plain_text",
                                            "text": "Select chapter",
                                            "emoji": True,
                                        },
                                        "options": options,
                                    }
                                ],
                            }
                        )
                    blocks.append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*"
                                + book_user.resource.chapters.first().name
                                + "*",
                            },
                        }
                    )

                    for i in book_user.resource.chapters.first().content.all():
                        blocks.append(i.to_slack_block(s.user_obj))
                    resource = book_user.resource.next_chapter(-1, "course" in value)
                    s.open_modal(
                        response["trigger_id"],
                        "Resource",
                        blocks,
                        callback=f"dialog:{type}:{book_user.id}:{resource.id}",
                        private_metadata="",
                        submit_name="Next",
                    )
                    return Response()

            # external form was completed and now triggered the complete to do function
            if "to_do:external" in value:
                to_do_user = ToDoUser.objects.get(
                    id=value.split(":")[2], user=s.user_obj
                )
                if len(to_do_user.form) == 0:
                    s.send_message(
                        text="Please complete the form first. Click on 'View details' to complete it."
                    )
                    return Response()
                items = to_do_user.mark_completed()
                s.send_sequence_triggers(items, to_do_user)
                new_blocks = []
                for i in response["message"]["blocks"]:
                    if i["block_id"] != str(to_do_user.id):
                        new_blocks.append(i)
                s.update_message(ts=response["message"]["ts"], blocks=new_blocks)
                return Response()

            # show resources based on category
            if "category" in value:
                if value.split(":")[1] == "-1":
                    books = ResourceUser.objects.filter(
                        user=s.user_obj, resource__category__isnull=True
                    )
                else:
                    category = Category.objects.get(id=int(value.split(":")[1]))
                    books = ResourceUser.objects.filter(
                        user=s.user_obj, resource__category=category
                    )
                blocks = s.format_resource_block(items=books, pre_message=None)
                s.send_message(blocks=blocks)
                return Response()

        # respond to a dialog completion
        if response["type"] == "view_submission":
            value = response["view"]["callback_id"]
            # save welcome message from colleague to new hire
            if "welcome" in value:
                new_hire = get_user_model().objects.get(id=value.split(":")[1])
                message = response["view"]["state"]["values"]["input"]["message"][
                    "value"
                ]
                w, created = NewHireWelcomeMessage.objects.get_or_create(
                    colleague=s.user_obj,
                    new_hire=new_hire,
                    defaults={"message": message},
                )
                if not created:
                    w.message = message
                    w.save()
                return Response()

            # save to do and optionally the form that got submitted with it
            if "to_do" in value:
                to_do_user = ToDoUser.objects.get(id=value.split(":")[2])
                form = to_do_user.to_do.form
                for i in form:
                    user_data = response["view"]["state"]["values"][i["id"]][i["id"]]
                    if user_data["type"] == "static_select":
                        i["answer"] = response["view"]["state"]["values"][i["id"]][
                            i["id"]
                        ]["selected_option"]["value"]
                    else:
                        i["answer"] = response["view"]["state"]["values"][i["id"]][
                            i["id"]
                        ]["value"]
                to_do_user.form = form
                to_do_user.save()
                items = to_do_user.mark_completed()
                s.send_sequence_triggers(items, to_do_user)
                s.update_to_do_message(
                    ts=value.split(":")[3],
                    block_ids=response["view"]["private_metadata"],
                    remove_item=to_do_user.id,
                )
                return Response()

            if "resource" in value or "course" in value:
                book_user = ResourceUser.objects.get(
                    user=s.user_obj, id=int(value.split(":")[2])
                )
                chapter = Chapter.objects.get(id=value.split(":")[3])
                # saving form
                if (
                    "state" in response["view"]
                    and "values" in response["view"]["state"]
                ):
                    form = ContentSerializer(chapter.content, many=True).data
                    answers = []
                    for i in form:
                        answers.append(
                            response["view"]["state"]["values"][str(i["id"])][
                                str(i["id"])
                            ]["selected_option"]["value"]
                        )
                    course_answer, cre = book_user.answers.get_or_create(
                        chapter=chapter, defaults={"answers": answers}
                    )
                    if not cre:
                        course_answer.answers = answers
                    else:
                        book_user.answers.add(course_answer)

                resource = book_user.book.next_chapter(
                    value.split(":")[3], "course" in value
                )
                book_user.add_step(resource)
                if resource is None:
                    return Response()
                view = s.create_updated_view(
                    resource.id, response["view"], book_user.completed_course
                )
                return Response({"response_action": "update", "view": view})

            if "approve:newhire" in value:
                new_hire = User.objects.get(
                    id=int(response["view"]["private_metadata"])
                )
                new_hire.role = 0
                new_hire.save()
                for i in response["view"]["state"]["values"]["seq"]["answers"][
                    "selected_options"
                ]:
                    seq = Sequence.objects.get(id=i["value"])
                    seq.assign_to_user(new_hire)
                s.client.chat_delete(channel=s.channel, ts=value.split(":")[2])

        return Response()
