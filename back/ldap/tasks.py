from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.formats import localize
from django.utils.translation import gettext as _

from admin.integrations.models import Integration
from organization.models import Organization, WelcomeMessage
from users.models import ResourceUser, ToDoUser
from .ldap import LdapConfig, inetOrgPerson, posixAccount,LDAP_OP


def ldap_init():
    ldap_config = LdapConfig()
    ldap_config.HOST = settings.LDAP_HOST
    ldap_config.PORT=settings.LDAP_PORT
    ldap_config.TLS=settings.TLS
    ldap_config.BASE_DN = settings.LDAP_BASE_DN
    ldap_config.BIND_DN = settings.LDAP_BIND_DN
    ldap_config.BIND_PW = settings.LDAP_BIND_PW
    ldap_config.USER_BASE_RDN = settings.LDAP_USER_BASE_RDN
    ldap_config.GROUP_BASE_RDN = settings.LDAP_GROUP_BASE_RDN
    ldap_config.USER_FILTER = settings.LDAP_USER_FILTER
    ldap_config.GROUP_FILTER = settings.LDAP_GROUP_FILTER
    return ldap_config


def user_2_ldap(user):
    ldap_user=inetOrgPerson(
        uid=user.username,
        sn=user.last_name,
        givenName=user.first_name,
        mail=user.email,
        telephoneNumber=user.phone_number,
    )
    if settings.LDAP_ACCOUNT_TYPE == "inetOrgPerson":
        return ldap_user
    else:
        ldap_user2=posixAccount(uid="",sn="",givenName="",mail="",telephoneNumber="")
        ldap_user2.copy_from(ldap_user)
        return ldap_user2

def ldap_add_user(users=[]):
    # Drop if LDAP is not enabled
    if (not settings.LDAP_SYNC):
        return

    ldap = LDAP_OP(ldap_init())
    org = Organization.object.get()

    if len(users) == 0:
        users = get_user_model().new_hires.without_ldap()

    for user in users:
        ldap_user=user_2_ldap(user)
        response = slack.find_by_email(email=user.email.lower())
        if response:
            translation.activate(user.language)
            user.slack_user_id = response["user"]["id"]
            user.save()

            # Personalized message for user (slack welcome message)
            blocks = [
                paragraph(
                    user.personalize(
                        WelcomeMessage.objects.get(
                            language=user.language, message_type=3
                        ).message
                    ),
                )
            ]

            # Check if extra buttons need to be send with it as well
            if org.slack_buttons:
                blocks.extend(get_new_hire_first_message_buttons())

            # Adding introduction items
            blocks.extend(
                [
                    SlackIntro(intro, user).format_block()
                    for intro in user.introductions.all()
                ]
            )

            res = Slack().send_message(
                blocks=blocks, text=_("Welcome!"), channel=user.slack_user_id
            )
            user.slack_channel_id = res["channel"]
            user.save()

            # Send user to do items for that day (and perhaps overdue ones)
            tasks = ToDoUser.objects.overdue(user) | ToDoUser.objects.due_today(user)

            if tasks.exists():
                blocks = SlackToDoManager(user).get_blocks(
                    tasks.values_list("id", flat=True),
                    text=_("These are the tasks you need to complete:"),
                )
                Slack().send_message(
                    blocks=blocks,
                    text=_("These are the tasks you need to complete:"),
                    channel=user.slack_user_id,
                )


def ldap_update_user():
    if (
        not Integration.objects.filter(integration=0).exists()
        and settings.SLACK_APP_TOKEN == ""
    ):
        return

    for user in get_user_model().new_hires.with_slack():
        local_datetime = user.get_local_time()

        if not (
            local_datetime.hour == 8
            and local_datetime.weekday() < 5
            and local_datetime.date() >= user.start_day
        ):
            continue

        translation.activate(user.language)

        overdue_items = ToDoUser.objects.overdue(user)
        tasks = ToDoUser.objects.due_today(user) | overdue_items

        courses_due = ResourceUser.objects.filter(
            user=user, resource__on_day__lte=user.workday
        )
        # Filter out completed courses
        course_blocks = [
            SlackResource(course, user).get_block()
            for course in courses_due
            if course.is_course
        ]

        if len(course_blocks):
            course_blocks.insert(
                0, paragraph(_("Here are some courses that you need to complete"))
            )
            Slack().send_message(
                blocks=course_blocks,
                text=_("Here are some courses that you need to complete"),
                channel=user.slack_user_id,
            )

        # If any overdue tasks exist, then notify the user
        if tasks.exists():
            if overdue_items.exists():
                text = _(
                    "Good morning! These are the tasks you need to complete. Some to "
                    "do items are overdue. Please complete those as soon as possible!"
                )
            else:
                text = _(
                    "Good morning! These are the tasks you need to complete today:"
                )

            blocks = SlackToDoManager(user).get_blocks(
                tasks.values_list("id", flat=True),
                text=text,
            )
            Slack().send_message(blocks=blocks, text=text, channel=user.slack_user_id)

def ldap_delete_user():
    pass