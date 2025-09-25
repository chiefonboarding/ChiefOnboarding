from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout

from admin.templates.forms import MultiSelectField, TagModelForm
from misc.mixins import FilterDepartmentsFieldByUserMixin
from users.selectors import get_all_users_for_departments_of_user

from .models import Introduction


class IntroductionForm(FilterDepartmentsFieldByUserMixin, TagModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.get("user")
        super().__init__(*args, **kwargs)
        self.fields["intro_person"].queryset = get_all_users_for_departments_of_user(
            user=user
        )
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name"),
                    Field("departments"),
                    MultiSelectField("tags"),
                    Field("intro_person"),
                    css_class="col-12",
                ),
                css_class="row",
            ),
        )

    class Meta:
        model = Introduction
        fields = ("name", "intro_person", "departments", "tags")
