import logging
import re

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str

from admin.integrations.utils import get_value_from_notation

logger = logging.getLogger(__name__)


class UserAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class MFAAdapter(DefaultMFAAdapter):
    def encrypt(self, text: str) -> str:
        # encrypt with secret key
        return Fernet(settings.SECRET_KEY).encrypt(force_bytes(text))

    def decrypt(self, encrypted_text: str) -> str:
        value = bytes(encrypted_text)
        return force_str(Fernet(settings.SECRET_KEY).decrypt(value))


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def _get_user_role(self, raw_role_data):
        roles = {
            get_user_model().Role.ADMIN: settings.OIDC_ROLE_ADMIN_PATTERN,
            get_user_model().Role.MANAGER: settings.OIDC_ROLE_MANAGER_PATTERN,
            get_user_model().Role.NEWHIRE: settings.OIDC_ROLE_NEW_HIRE_PATTERN,
        }
        for role, pattern in roles.items():
            if re.search(rf"{pattern}", raw_role_data):
                return role

        # if no matches, then make them "other"
        return get_user_model().Role.OTHER

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # set default to OTHER
        user_field(user, "role", get_user_model().Role.OTHER)

        if settings.OIDC_ROLE_PATH_IN_RETURN != "":
            try:
                raw_role_data = get_value_from_notation(
                    settings.OIDC_ROLE_PATH_IN_RETURN, data
                )
            except KeyError:
                # end here
                logger.info("OIDC: Path does not exist in the given data")
                return user

            user_field(user, "role", self._get_user_role(raw_role_data))

        return user
