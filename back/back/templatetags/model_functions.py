from django import template
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
import json

register = template.Library()


@register.simple_tag
def get_user_answer_by_chapter(resource_user, chapter, idx):
    # Get the user's answer for this chapter
    user_answer = resource_user.get_user_answer_by_chapter(chapter)
    if user_answer is None:
        return _("N/A")

    # Get the answer for this specific question
    try:
        user_given_answer = user_answer.answers[f"item-{idx}"]
    except (KeyError, AttributeError):
        return _("No answer found")

    # Get the question details
    questions = chapter.content["blocks"]
    if idx >= len(questions):
        return _("Question not found")

    question = questions[idx]
    question_type = question.get('question_type', 'multiple_choice')

    # Handle different question types
    if question_type == 'multiple_choice' or not question_type:
        # For multiple choice, find the selected option text
        for option in question.get("items", []):
            if option["id"] == user_given_answer:
                return option["text"]
        return _("Could not find selected option")

    elif question_type in ['file_upload', 'photo_upload']:
        # For file uploads, show a download link
        if isinstance(user_given_answer, dict):
            filename = user_given_answer.get('filename', 'file')
            url = user_given_answer.get('url', '#')
            file_type = user_given_answer.get('type', 'file_upload')

            if file_type == 'photo_upload' and url:
                # For images, show a thumbnail with a link
                return format_html(
                    '<div><a href="{}" target="_blank" class="d-block mb-2">'
                    '<img src="{}" alt="{}" style="max-width: 200px; max-height: 150px;" class="img-thumbnail">'
                    '</a><a href="{}" target="_blank" class="btn btn-sm btn-primary">'
                    '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-download" '
                    'width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" '
                    'fill="none" stroke-linecap="round" stroke-linejoin="round">'
                    '<path stroke="none" d="M0 0h24v24H0z" fill="none"></path>'
                    '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"></path>'
                    '<path d="M7 11l5 5l5 -5"></path>'
                    '<path d="M12 4l0 12"></path>'
                    '</svg> {}</a></div>',
                    url, url, filename, url, filename
                )
            else:
                # For other files, just show a download link
                return format_html(
                    '<a href="{}" target="_blank" class="btn btn-sm btn-primary">'
                    '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-download" '
                    'width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" '
                    'fill="none" stroke-linecap="round" stroke-linejoin="round">'
                    '<path stroke="none" d="M0 0h24v24H0z" fill="none"></path>'
                    '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"></path>'
                    '<path d="M7 11l5 5l5 -5"></path>'
                    '<path d="M12 4l0 12"></path>'
                    '</svg> {}</a>',
                    url, filename
                )
        return _("No file uploaded")

    elif question_type == 'fill_in_blank':
        # For fill in the blank, show the question with the answer filled in
        content = question.get('content', '')
        if content and user_given_answer:
            # Replace XXXX or [blank] with the user's answer, highlighted
            filled_content = content.replace('XXXX', f'<mark class="bg-success text-white px-1">{user_given_answer}</mark>')
            filled_content = filled_content.replace('[blank]', f'<mark class="bg-success text-white px-1">{user_given_answer}</mark>')

            # Show if the answer was correct
            correct_answer = question.get('correct_answer', '')
            is_correct = False

            if question.get('case_sensitive', False):
                is_correct = user_given_answer == correct_answer
            else:
                is_correct = user_given_answer.lower() == correct_answer.lower()

            if correct_answer:
                if is_correct:
                    return format_html('{} <span class="badge bg-success">Correct</span>', filled_content)
                else:
                    return format_html('{} <span class="badge bg-danger">Incorrect</span> <small class="text-muted">(Correct answer: {})</small>',
                                      filled_content, correct_answer)

            return format_html(filled_content)

        # Fallback to just showing the answer
        return user_given_answer

    elif question_type == 'free_text':
        # For free text, format with line breaks
        if isinstance(user_given_answer, str) and user_given_answer:
            # Replace newlines with HTML line breaks
            formatted_text = user_given_answer.replace('\n', '<br>')
            return format_html('<div class="p-3 bg-light rounded">{}</div>', formatted_text)
        return _("No text provided")

    elif question_type == 'rating_scale':
        # For rating scale, show the selected rating with stars or number
        if user_given_answer:
            rating = int(user_given_answer)
            max_rating = int(question.get('max_rating', 5))

            # Check if we should show labels
            if question.get('show_labels', True):
                min_label = question.get('min_label', 'Poor')
                max_label = question.get('max_label', 'Excellent')

                # If rating is min or max, show the label
                if rating == int(question.get('min_rating', 1)):
                    label = min_label
                elif rating == max_rating:
                    label = max_label
                else:
                    label = ""

                # Show stars for ratings
                stars_html = ''.join(['★' for _ in range(rating)]) + ''.join(['☆' for _ in range(max_rating - rating)])

                if label:
                    return format_html('<div>{} <span class="text-warning">{}</span> ({})</div>',
                                      rating, stars_html, label)
                else:
                    return format_html('<div>{} <span class="text-warning">{}</span></div>',
                                      rating, stars_html)
            else:
                # Just show the number
                return str(rating)
        return _("No rating provided")

    elif question_type == 'date_picker':
        # For date picker, format the date nicely
        if user_given_answer:
            # The date should already be in YYYY-MM-DD format
            return user_given_answer
        return _("No date selected")

    elif question_type == 'checkbox_list':
        # For checkbox list, show all selected options
        if isinstance(user_given_answer, list) and user_given_answer:
            selected_texts = []
            for option_id in user_given_answer:
                for option in question.get("items", []):
                    if option["id"] == option_id:
                        selected_texts.append(option["text"])

            if selected_texts:
                return format_html('<ul class="mb-0">{}</ul>',
                                  format_html(''.join([f'<li>{text}</li>' for text in selected_texts])))

        return _("No options selected")

    # Fallback for unknown question types
    if isinstance(user_given_answer, (dict, list)):
        return format_html('<pre>{}</pre>', json.dumps(user_given_answer, indent=2))

    return str(user_given_answer)
