from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='email_provider',
            field=models.CharField(
                blank=True,
                choices=[
                    ('smtp', 'SMTP'),
                    ('mailgun', 'Mailgun'),
                    ('mailjet', 'Mailjet'),
                    ('mandrill', 'Mandrill'),
                    ('postmark', 'Postmark'),
                    ('sendgrid', 'SendGrid'),
                    ('sendinblue', 'Sendinblue'),
                ],
                default='',
                help_text='Select which email provider to use for sending emails',
                max_length=20,
                verbose_name='Email Provider'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='default_from_email',
            field=models.CharField(
                blank=True,
                default='',
                help_text="The email address that will be used as the sender (e.g., 'onboarding@yourcompany.com' or 'Your Company <onboarding@yourcompany.com>')",
                max_length=255,
                verbose_name='Default From Email'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_host',
            field=models.CharField(
                blank=True,
                default='',
                help_text="SMTP server hostname (e.g., 'smtp.gmail.com')",
                max_length=255,
                verbose_name='SMTP Host'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_port',
            field=models.IntegerField(
                blank=True,
                default=587,
                help_text='SMTP server port (usually 25, 465, or 587)',
                null=True,
                verbose_name='SMTP Port'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_host_user',
            field=models.CharField(
                blank=True,
                default='',
                help_text='SMTP server username',
                max_length=255,
                verbose_name='SMTP Username'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_host_password',
            field=models.CharField(
                blank=True,
                default='',
                help_text='SMTP server password',
                max_length=255,
                verbose_name='SMTP Password'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_use_tls',
            field=models.BooleanField(
                default=True,
                help_text='Use TLS encryption for SMTP connection',
                verbose_name='Use TLS'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='email_use_ssl',
            field=models.BooleanField(
                default=False,
                help_text="Use SSL encryption for SMTP connection (don't enable both TLS and SSL)",
                verbose_name='Use SSL'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='mailgun_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Mailgun API Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='mailgun_domain',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Mailgun Domain'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='mailjet_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Mailjet API Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='mailjet_secret_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Mailjet Secret Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='mandrill_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Mandrill API Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='postmark_server_token',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Postmark Server Token'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='sendgrid_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='SendGrid API Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='sendinblue_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Sendinblue API Key'
            ),
        ),
    ]
