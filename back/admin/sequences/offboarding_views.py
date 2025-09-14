from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.list import ListView

from admin.sequences.models import Sequence
from users.mixins import ManagerPermMixin


class OffboardingSequenceListView(ManagerPermMixin, ListView):
    """
    Lists all onboarding sequences in a table.
    """

    template_name = "templates.html"
    queryset = Sequence.offboarding.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Offboarding sequence items")
        context["subtitle"] = ""
        context["add_action"] = reverse_lazy("sequences:offboarding-create")
        return context
