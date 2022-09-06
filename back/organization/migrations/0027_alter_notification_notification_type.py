# Generated by Django 3.2.13 on 2022-09-06 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0026_auto_20220830_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('added_todo', 'A new to do item has been added'), ('completed_todo', 'To do item has been marked as completed'), ('added_resource', 'A new resource item has been added'), ('completed_course', 'Course has been completed'), ('added_badge', 'A new badge item has been added'), ('added_introduction', 'A new introduction item has been added'), ('added_preboarding', 'A new preboarding item has been added'), ('added_appointment', 'A new appointment item has been added'), ('added_new_hire', 'A new hire has been added'), ('added_administrator', 'A new administrator has been added'), ('added_manager', 'A new manager has been added'), ('added_admin_task', 'A new admin task has been added'), ('sent_email_message', 'A new email has been sent'), ('sent_text_message', 'A new text message has been sent'), ('sent_slack_message', 'A new slack message has been sent'), ('updated_slack_message', 'A new slack message has been updated'), ('sent_email_login_credentials', 'Login credentials have been sent'), ('sent_email_task_reopened', 'Reopened task email has been sent'), ('sent_email_task_reminder', 'Task reminder email has been sent'), ('sent_email_new_hire_credentials', 'Sent new hire credentials email'), ('sent_email_preboarding_access', 'Sent new hire preboarding email'), ('sent_email_custom_sequence', 'Sent email from sequence'), ('sent_email_new_hire_with_updates', 'Sent email with updates to new hire'), ('sent_email_admin_task_extra', 'Sent email to extra person in admin task'), ('sent_email_admin_task_new_assigned', 'Sent email about new person assigned to admin task'), ('sent_email_admin_task_new_comment', 'Sent email about new comment on admin task'), ('sent_email_integration_notification', 'Sent email about completing integration call'), ('failed_no_phone', "Couldn't send text message: number is missing"), ('failed_no_email', "Couldn't send email message: email is missing"), ('failed_email_recipients_refused', "Couldn't deliver email message: recipient refused"), ('failed_email_delivery', "Couldn't deliver email message: provider error"), ('failed_email_address', "Couldn't deliver email message: provider error"), ('failed_send_slack_message', "Couldn't send Slack message"), ('failed_update_slack_message', "Couldn't update Slack message"), ('ran_integration', 'Integration has been triggered'), ('failed_integration', "Couldn't complete integration"), ('failed_text_integration_notification', "Couldn't send integration notification")], default='added_todo', max_length=100),
        ),
    ]
