from django.shortcuts import render

from django.views.generic import View
from users.mixins import AdminPermMixin, LoginRequiredMixin
from admin.templates.utils import get_templates_model

from django.shortcuts import get_object_or_404, redirect

class TemplateDuplicateView(LoginRequiredMixin, AdminPermMixin, View):

    def post(self, request, template_pk, template_type, *args, **kwargs):
        templates_model = get_templates_model(template_type)
        template_item = get_object_or_404(templates_model, id=template_pk)
        new_template_item = template_item.duplicate()
        return redirect(new_template_item.update_url())
