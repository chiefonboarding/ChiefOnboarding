from allauth.account.adapter import DefaultAccountAdapter
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.encoding import force_bytes, force_str


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
