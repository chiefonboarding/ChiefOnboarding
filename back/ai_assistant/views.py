from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from .agent import ChiefOnboardingAgent


class AIAssistantView(LoginRequiredMixin, TemplateView):
    template_name = "ai_assistant/chat.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["openai_configured"] = bool(getattr(settings, "OPENAI_API_KEY", None))
        return context


class AIAssistantChatView(LoginRequiredMixin, View):
    def post(self, request):
        import json

        try:
            data = json.loads(request.body)
            message = data.get("message", "")

            if not message:
                return JsonResponse({"error": "No message provided"}, status=400)

            session_key = f"ai_agent_{request.user.id}"

            if session_key not in request.session:
                agent = ChiefOnboardingAgent()
                request.session[session_key] = {
                    "conversation_history": agent.conversation_history
                }
            else:
                agent = ChiefOnboardingAgent()
                agent.conversation_history = request.session[session_key][
                    "conversation_history"
                ]

            response = agent.chat(message)

            request.session[session_key] = {
                "conversation_history": agent.conversation_history
            }
            request.session.modified = True

            return JsonResponse({"response": response, "success": True})

        except Exception as e:
            return JsonResponse({"error": str(e), "success": False}, status=500)


class AIAssistantResetView(LoginRequiredMixin, View):
    def post(self, request):
        session_key = f"ai_agent_{request.user.id}"
        if session_key in request.session:
            del request.session[session_key]
        return JsonResponse({"success": True, "message": "Conversation reset"})
