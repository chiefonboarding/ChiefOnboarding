from admin.users.models import User
from django.conf import settings

from admin.sequences.models import Condition, ExternalMessage

from .models import Organization


def org_include(request):
    try:
        return {
            "org": Organization.objects.first(),
            "DEBUG": settings.DEBUG,
            "ConditionType": Condition.Type.__dict__,
            "ExternalMessageType": ExternalMessage.Type.__dict__,
            "ExternalMessagesPersonType": ExternalMessage.PersonType.__dict__,
            "UserRole": User.Role.__dict__,
        }
    except Exception:
        # will only fail when user has not ran migrations yet. Org is set up during
        # setup
        return {"org": Organization.objects.none(), "DEBUG": settings.DEBUG}
