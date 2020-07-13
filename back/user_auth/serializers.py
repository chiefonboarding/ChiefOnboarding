from rest_auth.serializers import PasswordResetSerializer as OldPasswordResetSerializer


class PasswordResetSerializer(OldPasswordResetSerializer):
    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': 'Onboarding <hello@chiefonboarding.com>',
            'request': request,
            'extra_email_context': {'url': request.META['HTTP_HOST']},
            'email_template_name': 'email/reset.html',
            'subject_template_name': 'email/reset_subject.txt'
        }
        self.reset_form.save(**opts)
