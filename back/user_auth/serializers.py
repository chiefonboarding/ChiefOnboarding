from rest_auth.serializers import PasswordResetSerializer as OldPasswordResetSerializer
from rest_framework import serializers
from django.conf import settings

class PasswordResetSerializer(OldPasswordResetSerializer):
    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'request': request,
            'extra_email_context': {'url': request.META['HTTP_HOST']},
            'email_template_name': 'email/reset.html',
            'subject_template_name': 'email/reset_subject.txt'
        }
        self.reset_form.save(**opts)

class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField(max_length=200)
    password = serializers.CharField(max_length=10000)
    totp = serializers.CharField(default='', allow_blank=True)
