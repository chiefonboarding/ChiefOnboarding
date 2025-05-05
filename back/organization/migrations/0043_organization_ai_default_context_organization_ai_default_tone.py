# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0042_organization_ai_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='ai_default_context',
            field=models.TextField(
                blank=True,
                help_text="Default context for AI content generation (e.g., 'You are writing content for an employee onboarding platform')",
                verbose_name='AI Default Context',
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='ai_default_tone',
            field=models.CharField(
                blank=True,
                default='professional and friendly',
                help_text="Default tone for AI content generation (e.g., 'professional', 'friendly', 'casual')",
                max_length=100,
                verbose_name='AI Default Tone',
            ),
        ),
    ]
