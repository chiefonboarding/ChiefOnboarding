from django.template import Context, Template
from organization.models import Organization

from .models import EmailTemplate


def render_email_template(template_id, context_data):
    """
    Render an email template with the given context data.
    
    Args:
        template_id: The ID of the EmailTemplate to render
        context_data: A dictionary of context data to use for rendering
        
    Returns:
        A tuple of (subject, html_content) with the rendered email
    """
    try:
        template = EmailTemplate.objects.get(id=template_id)
        
        # Render the subject with the context
        subject_template = Template(template.subject)
        subject = subject_template.render(Context(context_data))
        
        # Get the organization's base email template
        org = Organization.object.get()
        
        # Convert the template content from JSON to the format expected by create_email
        content_blocks = []
        for block in template.content.get('blocks', []):
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
        
        # Add the user to the context for personalization
        if 'user' not in context_data and 'new_hire' in context_data:
            context_data['user'] = context_data['new_hire']
            
        # Create the email content
        context_data['content'] = content_blocks
        context_data['org'] = org
        html_content = org.create_email(context_data)
        
        return subject, html_content
    except EmailTemplate.DoesNotExist:
        return None, None
    except Exception as e:
        # Log the error
        print(f"Error rendering email template: {str(e)}")
        return None, None


def get_available_email_templates(category=None):
    """
    Get a list of available email templates, optionally filtered by category.
    
    Args:
        category: Optional category to filter by
        
    Returns:
        A queryset of EmailTemplate objects
    """
    if category:
        return EmailTemplate.objects.filter(category=category).order_by('name')
    return EmailTemplate.objects.all().order_by('category', 'name')
