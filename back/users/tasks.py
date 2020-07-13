from django.contrib.auth import get_user_model
from django.utils import translation

from back.celery import app
from organization.models import WelcomeMessage

from .emails import send_new_hire_cred


@app.task(bind=True)
def send_new_hire_credentials(self, user_id):
    user = get_user_model().objects.get(id=user_id)
    translation.activate(user.language)
    message = WelcomeMessage.objects.get(language=user.language, message_type=1).message
    send_new_hire_cred(user, message)
