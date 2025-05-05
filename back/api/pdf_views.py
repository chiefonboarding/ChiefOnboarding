import io
import json
import logging
import os
import base64
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import pdfplumber
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

        # Get organization settings for OpenAI API key
        org = Organization.objects.get()
        api_key = org.ai_api_key

        if not api_key:
            return JsonResponse({'error': 'AI API key not configured'}, status=400)

        # Extract text using pdfplumber (better text extraction)
        try:
            logger.info("Extracting text with pdfplumber")
            pdf_text = ""

            with pdfplumber.open(temp_file_path) as pdf:
                logger.info(f"Processing PDF with {len(pdf.pages)} pages")

                # Process all pages
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        pdf_text += f"--- Page {i+1} ---\n{page_text}\n\n"

            if pdf_text.strip():
                logger.info(f"Extracted {len(pdf_text)} characters of text from PDF")

                # Use a simpler, more direct prompt for question extraction
                questions = extract_questions_simple(pdf_text, api_key)

                if questions and len(questions) > 0:
                    logger.info(f"Successfully extracted {len(questions)} questions")
                    return JsonResponse({'questions': questions})
                else:
                    logger.info("No questions extracted, trying Vision API as fallback")
            else:
                logger.info("No text extracted with pdfplumber, trying Vision API")
        except Exception as e:
            logger.error(f"Error with pdfplumber extraction: {str(e)}")
            logger.info("Trying Vision API as fallback")

        # Fallback: Use Vision API for PDFs that are hard to extract text from
        try:
            logger.info("Using OpenAI Vision API as fallback")

            # Read the PDF file as base64
            with open(temp_file_path, "rb") as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

            # Check if the PDF is very large
            pdf_size_mb = len(pdf_base64) / (1024 * 1024)
            logger.info(f"PDF size: {pdf_size_mb:.2f} MB")

            # Use a simpler approach for large PDFs
            if pdf_size_mb > 4:
                logger.info("Large PDF detected, using simplified processing")
                # For large PDFs, we'll use pdfplumber to extract text and process with GPT-4
                # This should already have been attempted above, but we'll try with a different prompt
                with pdfplumber.open(temp_file_path) as pdf:
                    logger.info(f"Processing large PDF with {len(pdf.pages)} pages")
                    # Process first 10 pages only if there are many pages
                    max_pages = min(len(pdf.pages), 10)
                    pdf_text = ""
                    for i in range(max_pages):
                        page_text = pdf.pages[i].extract_text()
                        if page_text:
                            pdf_text += f"--- Page {i+1} ---\n{page_text}\n\n"

                if pdf_text.strip():
                    logger.info(f"Extracted {len(pdf_text)} characters from first {max_pages} pages")
                    # Use GPT-4 with a more focused prompt for large PDFs
                    questions = extract_questions_simple(pdf_text, api_key)
                    if questions and len(questions) > 0:
                        logger.info(f"Successfully extracted {len(questions)} questions from large PDF")
                        return JsonResponse({'questions': questions})

            # Use OpenAI's Vision API to analyze the PDF
            logger.info(f"Sending PDF to Vision API (size: {len(pdf_base64)} bytes)")
            vision_questions = extract_questions_with_vision_api(pdf_base64, api_key)

            if vision_questions and len(vision_questions) > 0:
                logger.info(f"Successfully extracted {len(vision_questions)} questions using Vision API")
                return JsonResponse({'questions': vision_questions})
            else:
                logger.warning("No questions extracted using any method")
                return JsonResponse({'error': 'Could not extract any questions from the PDF. Try a different file or format.'}, status=400)
        except Exception as e:
            logger.error(f"Error with Vision API extraction: {str(e)}")
            return JsonResponse({'error': 'Failed to extract questions from the PDF'}, status=500)

    except Exception as e:
        logger.error(f"Error extracting questions from PDF: {str(e)}")
        return JsonResponse({'error': 'Failed to process PDF'}, status=500)
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def extract_questions_with_vision_api(pdf_base64, api_key):
    """
    Use OpenAI's Vision API to extract questions directly from a PDF
    """
    try:
        # Prepare the prompt for OpenAI Vision API
        system_prompt = (
            "You are a helpful assistant that extracts items from PDF documents and converts them into multiple-choice questions. "
            "Your task is to identify ALL items that should be answered, checked off, or confirmed, including: "
            "- Explicit questions "
            "- Checklist items "
            "- Procedural instructions "
            "- Safety checks "
            "- Any other items that require confirmation or response "
            "For each item, create a question and provide 3-5 possible answer options. "
            "Format your response as a JSON array of objects, where each object has "
            "\"content\" (the question text) and \"items\" (an array of option texts). "
            "Process the entire document and extract items from ALL pages. "
            "Make sure to thoroughly analyze every page of the document."
        )

        # Call OpenAI Vision API
        logger.info("Calling Vision API with improved prompt for extracting all types of items")
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4-vision-preview',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': 'Extract all checklist items, procedural instructions, and questions from this document, even if they are not phrased as questions. Convert each item into a multiple-choice question with 3-5 options. Make sure to process ALL pages of the document, not just the first page. Group items by section if applicable.'},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f"data:application/pdf;base64,{pdf_base64}",
                                    'detail': 'high'
                                }
                            }
                        ]
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 4000
            },
            timeout=180  # Increased timeout for larger PDFs
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
                logger.error(f"Failed to parse Vision API response as JSON: {ai_response}")
                logger.error(f"JSON error: {str(e)}")
                return []
        else:
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"OpenAI Vision API error: {error_message}")
            return []

    except requests.RequestException as e:
        logger.error(f"Vision API request error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in extract_questions_with_vision_api: {str(e)}")
        return []

def extract_questions_simple(text, api_key):
    """
    Use a simpler, more direct approach to extract questions from text
    """
    try:
        # Log the number of pages in the text
        page_count = text.count("--- Page")
        logger.info(f"Extracting questions from text with {page_count} pages")

        # Prepare the prompt for OpenAI
        system_prompt = (
            "You are a helpful assistant that extracts items from text and converts them into multiple-choice questions. "
            "Your task is to identify ALL items that should be answered, checked off, or confirmed, including: "
            "- Explicit questions "
            "- Checklist items "
            "- Procedural instructions "
            "- Safety checks "
            "- Any other items that require confirmation or response "
            "For each item, create a question and provide 3-5 possible answer options. "
            "Format your response as a JSON array of objects, where each object has "
            "\"content\" (the question text) and \"items\" (an array of 3-5 possible answers as strings). "
            "Make sure to process ALL pages in the document, not just the first page."
        )

        user_prompt = (
            "Extract all checklist items, procedural instructions, and questions from the following multi-page text, "
            "even if they are not phrased as questions. Convert each item into a multiple-choice question with 3-5 options. "
            "The text is divided into pages with '--- Page X ---' markers. "
            "Make sure to process ALL pages, not just the first one. Group items by section if applicable.\n\n"
            f"{text}"
        )

        # Call OpenAI API
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4-turbo',  # Using GPT-4 for better extraction
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.2,  # Lower temperature for more focused extraction
                'max_tokens': 4000
            },
            timeout=120  # Increased timeout for larger documents
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
                logger.error(f"Failed to parse AI response as JSON: {ai_response}")
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
        logger.error(f"Unexpected error in extract_questions_simple: {str(e)}")
        return []

def extract_questions_with_openai(text, api_key):
    """Use OpenAI to extract questions and options from text"""
    try:
        # Log the number of pages in the text
        page_count = text.count("--- Page")
        logger.info(f"Extracting questions with OpenAI from text with {page_count} pages")

        # Prepare the prompt for OpenAI
        system_prompt = (
            "You are a helpful assistant that extracts items from text and converts them into multiple-choice questions. "
            "Your task is to identify ALL items that should be answered, checked off, or confirmed, including: "
            "- Explicit questions "
            "- Checklist items "
            "- Procedural instructions "
            "- Safety checks "
            "- Any other items that require confirmation or response "
            "For each item, create a question and provide 3-5 possible answer options. "
            "Format your response as a JSON array of objects, where each object has "
            "\"content\" (the question text) and \"items\" (an array of option texts). "
            "Process the entire text and extract items from ALL pages."
        )

        user_prompt = (
            "Extract all checklist items, procedural instructions, and questions from the following multi-page text, "
            "even if they are not phrased as questions. Convert each item into a multiple-choice question with 3-5 options. "
            "Make sure to process the entire text and extract items from ALL pages. "
            "The text is divided into pages with '--- Page X ---' markers. Group items by section if applicable.\n\n"
            f"{text}"
        )

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo-16k',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 4000
            },
            timeout=120  # Increased timeout for larger documents
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
