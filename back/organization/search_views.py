from organization.models import TemplateManager
from django.views.generic.base import TemplateView
from django.db.models import Q
from users.mixins import LoginRequiredMixin, ManagerPermMixin

from admin.to_do.models import ToDo
from admin.resources.models import Resource
from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.integrations.models import Integration
from admin.sequences.models import Sequence
from admin.hardware.models import Hardware
from users.models import User


class SearchHXView(LoginRequiredMixin, ManagerPermMixin, TemplateView):
    template_name = "search_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        if query == "":
            return context

        lookup_models = [
            ToDo, Resource, Badge, Introduction, Preboarding, Integration, Sequence, Hardware, User
        ]
        results = []
        for model in lookup_models:
            if model == User:
                objects = model.objects.filter(
                    Q(first_name__search=query) | Q(last_name__search=query)
                )
            elif hasattr(model, "templates") and isinstance(model.template, TemplateManager):
                objects = model.templates.filter(name__search=query)
            else:
                objects = model.objects.filter(name__search=query)
            results += [
                {"name": obj.name, "url": obj.update_url, "icon": obj.get_icon_template}
                for obj in objects
            ]

        context["results"] = results[:20]
        context["more_results"] = len(results) > 20
        return context
