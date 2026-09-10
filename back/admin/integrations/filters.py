import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

PAGINATE_BY_CHOICES = [("10", "10"), ("25", "25"), ("50", "50"), ("100", "100")]


class AccessReportFilter(django_filters.FilterSet):
    role = django_filters.MultipleChoiceFilter(
        choices=get_user_model().Role.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": _("Search by name or email")}),
    )

    is_active = django_filters.BooleanFilter(
        widget=forms.Select(choices=[("unknown", "All"), (True, "Yes"), (False, "No")])
    )

    per_page = django_filters.ChoiceFilter(
        choices=PAGINATE_BY_CHOICES,
        method="noop",
        label="Per page",
        empty_label=None,
    )

    class Meta:
        model = get_user_model()
        fields = ["role", "search", "is_active"]

    def noop(self, queryset, name, value):
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["is_active"].label = _("Has access to dashboard/slack bot")
        self.form.helper = FormHelper()
        self.form.helper.form_method = "get"
        self.form.helper.layout = Layout(
            Row(
                Column("role", css_class="col-md-2"),
                Column("search", css_class="col-md-3"),
                Column("is_active", css_class="col-md-3"),
                Column("per_page", css_class="col-md-2"),
                Column(
                    Submit("submit", _("Apply"), css_class="btn btn-primary"),
                    css_class="col-md-2 mt-5 d-flex align-items-start",
                ),
                css_class="g-2",
            )
        )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )
