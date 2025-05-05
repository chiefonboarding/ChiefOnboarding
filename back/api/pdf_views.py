import io
import json
import logging
import os
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import PyPDF2
import requests
from organization.models import Organization

logger = logging.getLogger(__name__)

@csrf_protect
@require_POST
@login_required
def extract_questions_from_pdf(request):
    """
    API endpoint to extract questions from a PDF using OpenAI.
    The PDF is stored temporarily and deleted after processing.
    """
    temp_file_path = None
    try:
        # Get the uploaded PDF file
        pdf_file = request.FILES.get('pdf_file')
        if not pdf_file:
            return JsonResponse({'error': 'PDF file is required'}, status=400)
        
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Extract text from the PDF
        pdf_text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(temp_file_path)
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return JsonResponse({'error': 'Failed to extract text from PDF'}, status=400)
        
        # Get organization settings for OpenAI API key
        org = Organization.object.get()
        api_key = org.ai_api_key
        
        if not api_key:
            return JsonResponse({'error': 'AI API key not configured'}, status=400)
        
        # Send text to OpenAI to extract questions
        questions = extract_questions_with_openai(pdf_text, api_key)
        
        return JsonResponse({'questions': questions})
        
    except Exception as e:
        logger.error(f"Error extracting questions from PDF: {str(e)}")
        return JsonResponse({'error': 'Failed to process PDF'}, status=500)
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def extract_questions_with_openai(text, api_key):
    """Use OpenAI to extract questions and options from text"""
    try:
        # Prepare the prompt for OpenAI
        system_prompt = (
            "You are a helpful assistant that extracts multiple-choice questions from text. "
            "For each question, identify the question text and all possible options. "
            "Format your response as a JSON array of objects, where each object has "
            "\"content\" (the question text) and \"items\" (an array of option texts)."
        )
        
        user_prompt = (
            "Extract all multiple-choice questions from the following text. "
            "If there are no clear questions, create appropriate multiple-choice questions "
            "based on the key concepts in the text.\n\n"
            f"{text}"
        )
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 2000
            },
            timeout=30
        )
        
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            ai_response = response_data['choices'][0]['message']['content']
            
            # Try to parse the JSON response
            try:
                # Find JSON in the response (in case OpenAI adds explanatory text)
                import re
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    ai_response = json_match.group(0)
                
                questions_data = json.loads(ai_response)
                
                # Format questions for the frontend
                formatted_questions = []
                for i, q in enumerate(questions_data):
                    # Generate a unique ID for the question
                    question_id = f"q-{i+1}-{os.urandom(4).hex()}"
                    
                    # Ensure we have the expected fields
                    question_content = q.get('content', '')
                    question_items = q.get('items', [])
                    
                    # If items is a list of strings, convert to objects
                    items = []
                    for j, item in enumerate(question_items):
                        if isinstance(item, str):
                            item_id = f"option-{j+1}-{os.urandom(4).hex()}"
                            items.append({'id': item_id, 'text': item})
                        else:
                            # If it's already an object, ensure it has an id
                            item_id = item.get('id', f"option-{j+1}-{os.urandom(4).hex()}")
                            items.append({'id': item_id, 'text': item.get('text', '')})
                    
                    question = {
                        'id': question_id,
                        'type': 'question',
                        'content': question_content,
                        'items': items
                    }
                    
                    # Set the first option as the default answer
                    if question['items']:
                        question['answer'] = question['items'][0]['id']
                    
                    formatted_questions.append(question)
                
                return formatted_questions
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {ai_response}")
                logger.error(f"JSON error: {str(e)}")
                return []
        else:
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"OpenAI API error: {error_message}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in extract_questions_with_openai: {str(e)}")
        return []
