from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0045_merge_20250506_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='mailersend_api_key',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='MailerSend API Key'
            ),
        ),
        migrations.AlterField(
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
                    ('mailersend', 'MailerSend'),
                ],
                default='',
                help_text='Select which email provider to use for sending emails',
                max_length=20,
                verbose_name='Email Provider'
            ),
        ),
    ]
