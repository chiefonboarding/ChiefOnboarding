from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0047_alter_organization_custom_email_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='storage_provider',
            field=models.CharField(
                choices=[('local', 'Local Storage'), ('s3', 'Amazon S3 or Compatible')],
                default='local',
                help_text='Select which storage provider to use for file uploads',
                max_length=20,
                verbose_name='Storage Provider'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='s3_endpoint_url',
            field=models.CharField(
                blank=True,
                default='https://s3.amazonaws.com',
                help_text="The endpoint URL for S3 or S3-compatible storage (e.g., 'https://s3.amazonaws.com')",
                max_length=255,
                verbose_name='S3 Endpoint URL'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='s3_access_key',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Access key for S3 or S3-compatible storage',
                max_length=255,
                verbose_name='S3 Access Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='s3_secret_key',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Secret key for S3 or S3-compatible storage',
                max_length=255,
                verbose_name='S3 Secret Key'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='s3_bucket_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Bucket name for S3 or S3-compatible storage',
                max_length=255,
                verbose_name='S3 Bucket Name'
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='s3_region',
            field=models.CharField(
                blank=True,
                default='us-east-1',
                help_text="Region for S3 or S3-compatible storage (e.g., 'us-east-1')",
                max_length=255,
                verbose_name='S3 Region'
            ),
        ),
    ]
