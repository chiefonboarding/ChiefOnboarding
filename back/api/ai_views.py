import json
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from organization.models import Organization

logger = logging.getLogger(__name__)

@require_POST
@login_required
@ensure_csrf_cookie
def generate_ai_content(request):
    """
    API endpoint to generate content using AI
    """
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        content_type = data.get('content_type', 'general')  # 'general', 'email', etc.

        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        # Get organization settings
        org = Organization.object.get()
        api_key = org.ai_api_key
        default_context = org.ai_default_context or 'You are a helpful assistant that generates content for an employee onboarding platform.'
        default_tone = org.ai_default_tone or 'professional and friendly'

        if not api_key:
            return JsonResponse({'error': 'AI API key not configured'}, status=400)

        # Prepare system message with context and tone
        system_message = f"{default_context} Write in a {default_tone} tone. "

        # Add content type specific instructions
        if content_type == 'email':
            system_message += (
                "You are generating content for an email template. "
                "Create professional, well-structured email content that is clear, concise, and engaging. "
                "Format the content appropriately for an email with proper greeting, body, and closing. "
                "The content should be suitable for HTML email format. "
            )

        # Add information about variables
        system_message += (
            "The content may include variables like {{first_name}}, {{last_name}}, {{position}}, "
            "{{department}}, {{manager}}, {{manager_email}}, {{buddy}}, {{buddy_email}}, and {{start}} "
            "which will be replaced with actual user data. Use these variables appropriately to personalize the content."
        )

        # Call OpenAI API
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': system_message},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 800  # Increased for email templates which might be longer
                },
                timeout=15  # Increased timeout for longer content
            )

            response_data = response.json()

            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']

                # Format content as HTML paragraphs
                # More sophisticated formatting for email content
                if content_type == 'email':
                    # Split by double newlines to identify paragraphs
                    paragraphs = content.split('\n\n')
                    formatted_paragraphs = []

                    for paragraph in paragraphs:
                        # Check if this is a greeting or signature line (typically shorter)
                        if len(paragraph.strip()) < 50 and ('Hello' in paragraph or 'Hi' in paragraph or 'Dear' in paragraph or 'Regards' in paragraph or 'Sincerely' in paragraph):
                            formatted_paragraphs.append(f'<p>{paragraph.replace(chr(10), "<br>")}</p>')
                        else:
                            # Regular paragraph
                            formatted_paragraphs.append(f'<p>{paragraph.replace(chr(10), "<br>")}</p>')

                    formatted_content = ''.join(formatted_paragraphs)
                else:
                    # Standard formatting for other content types
                    formatted_content = '<p>' + content.replace('\n\n', '</p><p>').replace(chr(10), '<br>') + '</p>'

                return JsonResponse({'content': formatted_content})
            else:
                logger.error(f"Unexpected API response: {response_data}")
                return JsonResponse({'error': 'Failed to generate content'}, status=500)

        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return JsonResponse({'error': 'Failed to connect to AI service'}, status=500)

    except Exception as e:
        logger.error(f"Error generating AI content: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
