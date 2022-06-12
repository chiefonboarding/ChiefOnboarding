from django.contrib.auth import get_user_model
from django.utils import translation
from django_q.tasks import async_task

from organization.models import Organization

from .emails import send_new_hire_credentials


def send_new_hire_creds(user_id):
    user = get_user_model().objects.get(id=user_id)
    translation.activate(user.language)
    send_new_hire_credentials(user.id)


def hourly_check_for_new_hire_send_credentials():
    org = Organization.object.get()

    # if sending of email credentials is disabled, then drop this task
    if not org.new_hire_email:
        return

    for new_hire in get_user_model().new_hires.all():
        new_hire_datetime = new_hire.get_local_time()
        if (
            new_hire_datetime.date() == new_hire.start_day
            and new_hire_datetime.hour == 8
        ):
            # Trigger task above to schedule sending credentials
            # In case an email address is incorrect (or not available), it will
            # not block the rest of the emails
            async_task(
                "users.tasks.send_new_hire_creds",
                new_hire.id,
                task_name=f"Sending login credentials: {new_hire.full_name}",
            )
