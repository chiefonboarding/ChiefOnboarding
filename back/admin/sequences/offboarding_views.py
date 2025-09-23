from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.list import ListView

from admin.sequences.selectors import (
    get_offboarding_sequences_for_user,
)
from users.mixins import AdminOrManagerPermMixin


class OffboardingSequenceListView(AdminOrManagerPermMixin, ListView):
    """
    Lists all onboarding sequences in a table.
    """

    template_name = "templates.html"
    paginate_by = 10

    def get_queryset(self):
        return get_offboarding_sequences_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Offboarding sequence items")
        context["subtitle"] = ""
        context["add_action"] = reverse_lazy("sequences:offboarding-create")
        return context
