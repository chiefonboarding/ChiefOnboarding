import json
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.decorators import login_required

from users.mixins import AdminPermMixin, LoginRequiredMixin
from users.models import User

from .forms import EmailTemplateForm
from .models import EmailTemplate
from .utils import render_email_template


class EmailTemplateListView(LoginRequiredMixin, AdminPermMixin, ListView):
    model = EmailTemplate
    template_name = "email_templates_list.html"
    context_object_name = "email_templates"

    def get_queryset(self):
        return EmailTemplate.objects.all().order_by("category", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Email Templates")
        context["subtitle"] = _("settings")
        return context


class EmailTemplateCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "email_template_form.html"
    success_url = reverse_lazy("settings:email-templates")
    success_message = _("Email template has been created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create Email Template")
        context["subtitle"] = _("settings")
        return context


class EmailTemplateUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "email_template_form.html"
    success_url = reverse_lazy("settings:email-templates")
    success_message = _("Email template has been updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Update Email Template")
        context["subtitle"] = _("settings")
        return context


class EmailTemplateDeleteView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, DeleteView
):
    model = EmailTemplate
    template_name = "email_template_confirm_delete.html"
    success_url = reverse_lazy("settings:email-templates")
    success_message = _("Email template has been deleted")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete Email Template")
        context["subtitle"] = _("settings")
        return context


@login_required
@require_POST
def preview_email_template(request):
    """
    Preview an email template with sample data
    """
    try:
        data = json.loads(request.body)
        template_content = data.get('content', {})
        subject = data.get('subject', 'Sample Email Subject')

        # Create a sample user for preview
        sample_user = {
            'first_name': 'John',
            'last_name': 'Doe',
            'position': 'Software Developer',
            'department': 'Engineering',
            'manager': 'Jane Smith',
            'manager_email': 'jane.smith@example.com',
            'buddy': 'Mike Johnson',
            'buddy_email': 'mike.johnson@example.com',
            'start': '2023-06-01',
            'email': 'john.doe@example.com',
        }

        # Create context for rendering
        context = {
            'user': sample_user,
            'new_hire': sample_user,
        }

        # Get the organization
        from organization.models import Organization
        org = Organization.objects.get()

        # Convert the template content to the format expected by create_email
        content_blocks = []
        for block in template_content.get('blocks', []):
            if block['type'] == 'paragraph':
                content_blocks.append({
                    'type': 'paragraph',
                    'data': {
                        'text': block['data']['text']
                    }
                })
            elif block['type'] == 'header':
                content_blocks.append({
                    'type': 'header',
                    'data': {
                        'text': block['data']['text'],
                        'level': block['data']['level']
                    }
                })
            elif block['type'] == 'list':
                content_blocks.append({
                    'type': 'list',
                    'data': {
                        'style': block['data']['style'],
                        'items': block['data']['items']
                    }
                })
            # Add other block types as needed

        # Create the email content
        context['content'] = content_blocks
        context['org'] = org
        html_content = org.create_email(context)

        # Render the subject with the context
        from django.template import Context, Template
        subject_template = Template(subject)
        rendered_subject = subject_template.render(Context(context))

        return JsonResponse({
            'subject': rendered_subject,
            'html_content': html_content
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
