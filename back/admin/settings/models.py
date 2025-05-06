from django.db import models
from django.utils.translation import gettext_lazy as _

class EmailTemplate(models.Model):
    """
    Model to store email templates that can be used for various email notifications.
    """
    class Category(models.TextChoices):
        WELCOME = 'welcome', _('Welcome Emails')
        TASK = 'task', _('Task Notifications')
        REMINDER = 'reminder', _('Reminders')
        CUSTOM = 'custom', _('Custom')
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Template Name")
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_("Email Subject")
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.CUSTOM,
        verbose_name=_("Category")
    )
    content = models.JSONField(
        default=dict,
        verbose_name=_("Email Content"),
        help_text=_("Content in Editor.js JSON format")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Internal description of when this template should be used")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Email Template")
        verbose_name_plural = _("Email Templates")
        ordering = ['name']
    
    def __str__(self):
        return self.name
