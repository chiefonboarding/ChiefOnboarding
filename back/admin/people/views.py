from django.views.generic.list import ListView

from users.models import User


class NewHireListView(ListView):
    template_name = "new_hires.html"
    queryset = User.new_hires.all().order_by("-start_day")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "New hires"
        context['subtitle'] = "people"
        return context

