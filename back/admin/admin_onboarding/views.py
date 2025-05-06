import json

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from users.mixins import AdminPermMixin, LoginRequiredMixin
from users.models import ToDoUser, ResourceUser

from .models import AdminOnboardingStatus
from .utils import mark_admin_onboarding_completed


class AdminOnboardingCompleteView(LoginRequiredMixin, AdminPermMixin, View):
    """
    View to mark the admin onboarding as completed.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if mark_admin_onboarding_completed(request.user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            messages.success(request, _("Admin onboarding marked as completed."))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error'}, status=500)
            messages.error(request, _("Failed to mark admin onboarding as completed."))

        return redirect("admin:new_hires")


class AdminOnboardingContentView(LoginRequiredMixin, AdminPermMixin, View):
    """
    View to get the admin onboarding content.
    """
    def get(self, request, *args, **kwargs):
        try:
            status = AdminOnboardingStatus.objects.get(admin=request.user)

            if status.status != AdminOnboardingStatus.Status.IN_PROGRESS:
                return JsonResponse({'status': 'completed'})

            # Get the to-do items and resources assigned to the admin
            todo_items = ToDoUser.objects.filter(user=request.user).select_related('to_do')
            resource_items = ResourceUser.objects.filter(user=request.user).select_related('resource')

            # Format the items for the overlay
            items = []

            # Add welcome step
            items.append({
                'title': _('Welkom bij ChiefOnboarding'),
                'content': _('''
                <div class="onboarding-content-section">
                    <h3>Welkom bij uw nieuwe onboarding platform!</h3>

                    <p>Fijn dat u heeft gekozen voor ChiefOnboarding. Deze interactieve gids helpt u om snel vertrouwd te raken met het systeem, zodat u direct aan de slag kunt met het creëren van geweldige onboarding ervaringen voor uw nieuwe medewerkers.</p>

                    <div class="onboarding-highlight-box">
                        <h4>Wat u gaat leren:</h4>
                        <ul>
                            <li>Navigeren door het dashboard</li>
                            <li>Begrijpen van de kernconcepten</li>
                            <li>Opzetten van uw eerste onboarding proces</li>
                            <li>Beheren van nieuwe medewerkers</li>
                        </ul>
                    </div>

                    <p>Klik op "Volgende" om te beginnen met uw reis door ChiefOnboarding!</p>
                </div>
                ''')
            })

            # Add steps for resources
            for resource_user in resource_items:
                resource = resource_user.resource
                chapters = resource.chapters.all().order_by('order')

                for chapter in chapters:
                    items.append({
                        'title': chapter.name,
                        'content': self.format_content(chapter.content)
                    })

            # Add steps for to-do items
            for todo_user in todo_items:
                todo = todo_user.to_do
                items.append({
                    'title': todo.name,
                    'content': self.format_content(todo.content)
                })

            # Add final step
            items.append({
                'title': _('Gefeliciteerd!'),
                'content': _('''
                <div class="onboarding-content-section">
                    <div class="onboarding-success">
                        <h3>🎉 Geweldig gedaan! U heeft de admin onboarding voltooid!</h3>

                        <p>U bent nu klaar om ChiefOnboarding volledig te gaan gebruiken en geweldige onboarding ervaringen te creëren voor uw nieuwe medewerkers.</p>

                        <div class="onboarding-highlight-box">
                            <h4>Wat u nu kunt doen:</h4>
                            <ul>
                                <li>Een volledige onboarding sequentie maken</li>
                                <li>Templates toevoegen voor verschillende afdelingen</li>
                                <li>Uw eerste nieuwe medewerker toevoegen</li>
                                <li>De documentatie bekijken voor geavanceerde functies</li>
                            </ul>
                        </div>

                        <p>Heeft u nog vragen? Bekijk de <a href="https://docs.chiefonboarding.com" target="_blank">documentatie</a> of neem contact op met ondersteuning.</p>

                        <div class="onboarding-final-cta">
                            <p>Klik op "Voltooien" om de onboarding af te ronden en aan de slag te gaan!</p>
                        </div>
                    </div>
                </div>
                ''')
            })

            return JsonResponse({
                'status': 'in_progress',
                'items': items
            })

        except AdminOnboardingStatus.DoesNotExist:
            return JsonResponse({'status': 'not_started'})

    def format_content(self, content):
        """Format the content for display in the overlay."""
        if not content or not isinstance(content, dict) or 'blocks' not in content:
            return ''

        html = '<div class="onboarding-content-section">'

        for block in content.get('blocks', []):
            if block.get('type') == 'paragraph':
                text = block.get('data', {}).get('text', '')
                # Check if it's a heading-like paragraph
                if text.startswith('# '):
                    text = text.replace('# ', '', 1)
                    html += f"<h3>{text}</h3>"
                elif text.startswith('## '):
                    text = text.replace('## ', '', 1)
                    html += f"<h4>{text}</h4>"
                elif text.startswith('### '):
                    text = text.replace('### ', '', 1)
                    html += f"<h5>{text}</h5>"
                else:
                    html += f"<p>{text}</p>"
            elif block.get('type') == 'header':
                level = block.get('data', {}).get('level', 2)
                text = block.get('data', {}).get('text', '')
                html += f"<h{level}>{text}</h{level}>"
            elif block.get('type') == 'list':
                items = block.get('data', {}).get('items', [])
                list_type = 'ol' if block.get('data', {}).get('style', 'unordered') == 'ordered' else 'ul'
                html += f'<div class="onboarding-highlight-box"><{list_type}>'
                for item in items:
                    html += f"<li>{item}</li>"
                html += f"</{list_type}></div>"
            elif block.get('type') == 'delimiter':
                html += '<hr class="onboarding-divider">'
            elif block.get('type') == 'quote':
                text = block.get('data', {}).get('text', '')
                caption = block.get('data', {}).get('caption', '')
                html += f'<blockquote class="onboarding-quote"><p>{text}</p>'
                if caption:
                    html += f'<footer>{caption}</footer>'
                html += '</blockquote>'
            elif block.get('type') == 'image':
                url = block.get('data', {}).get('file', {}).get('url', '')
                caption = block.get('data', {}).get('caption', '')
                if url:
                    html += f'<div class="onboarding-image-container"><img src="{url}" alt="{caption}" class="onboarding-image">'
                    if caption:
                        html += f'<div class="onboarding-image-caption">{caption}</div>'
                    html += '</div>'

        html += '</div>'
        return html
