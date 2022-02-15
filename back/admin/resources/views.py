from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from users.mixins import AdminPermMixin, LoginRequiredMixin

from .forms import ResourceForm
from .models import Resource, Chapter


class ResourceListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Resource.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Resource items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("resources:create")
        return context


class ResourceCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    success_message = "Resource item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create resource item"
        context["subtitle"] = "templates"
        return context


class ResourceUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "resource_update.html"
    form_class = ResourceForm
    success_url = reverse_lazy("resources:list")
    queryset = Resource.templates.all()
    success_message = "Resource item has been updated"
    counter = 0

    def _create_or_update_chapter(self, resource, parent, chapter):
        if isinstance(chapter['id'], int):
            chap = Chapter.objects.get(id=chapter['id'])
            chap.name = chapter['name']
            chap.content = chapter['content']
            chap.resource = resource
            chap.order = self.counter
            chap.save()
        else:
            chap = Chapter.objects.create(
                resource=resource,
                name=chapter['name'],
                content=chapter['content'],
                type=chapter['type'],
                order=self.counter
            )
            if parent is not None:
                chap.parent_chapter = Chapter.objects.get(id=parent)
                chap.save()
        self.counter += 1

        # Return new/updated item id
        return chap.id

    def _get_child_chapters(self, resource, parent, children):
        if len(children) == 0:
            return

        for chapter in children:
            # Save or update item
            parent_id = self._create_or_update_chapter(resource, parent, chapter)

            # Go one level deeper - check and create chapters
            self._get_child_chapters(resource, parent_id, chapter['children'])


    @transaction.atomic
    def form_valid(self, form):
        resource = form.instance
        chapters = form.cleaned_data['chapters']
        # Detach all chapters and start rebuilding
        Chapter.objects.filter(resource=resource).update(resource=None)
        # Root chapters
        for chapter in chapters:
            parent_id = self._create_or_update_chapter(resource, None, chapter)

            self._get_child_chapters(resource, parent_id, chapter['children'])

        return super(ResourceUpdateView, self).form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update resource item"
        context["subtitle"] = "templates"
        return context


class ResourceDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Resource.objects.all()
    success_url = reverse_lazy("resources:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Resource item has been removed")
        return response
