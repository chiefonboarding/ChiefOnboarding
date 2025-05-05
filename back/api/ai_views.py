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
        system_message += "The content may include variables like {{first_name}}, {{last_name}}, {{position}}, {{department}}, {{manager}}, and {{buddy}} which will be replaced with actual user data."

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
                    'max_tokens': 500
                },
                timeout=10
            )

            response_data = response.json()

            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                # Format content as HTML paragraphs
                formatted_content = '<p>' + content.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
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
