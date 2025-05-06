from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0047_alter_organization_custom_email_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='logo_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='URL to an external logo image. This will be used instead of an uploaded logo if provided.',
                max_length=500,
                verbose_name='Logo URL'
            ),
        ),
    ]
