# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0041_alter_organization_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='ai_api_key',
            field=models.CharField(
                blank=True,
                help_text='API key for AI content generation (e.g., OpenAI API key)',
                max_length=255,
                verbose_name='AI API Key',
            ),
        ),
    ]
