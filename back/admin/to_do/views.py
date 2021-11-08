from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView

from misc.serializers import ContentSerializer
from .models import ToDo
from .serializers import ToDoSerializer
from .forms import ToDoForm


class ToDoListView(ListView):
    template_name = "templates.html"
    queryset = ToDo.templates.all().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "To do items"
        context['subtitle'] = "templates"
        context['add_action'] = reverse_lazy("todo:create")
        context['wysiwyg'] = []
        return context


class ToDoCreateView(SuccessMessageMixin, CreateView):
    template_name = "todo_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    success_message = "To do item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Create to do item"
        context['subtitle'] = "templates"
        return context


class ToDoUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "todo_update.html"
    form_class = ToDoForm
    success_url = reverse_lazy("todo:list")
    queryset = ToDo.templates.all()
    success_message = "To do item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Update to do item"
        context['subtitle'] = "templates"
        context['wysiwyg'] = ContentSerializer(context['todo'].content, many=True).data
        return context


class ToDoViewSet(viewsets.ModelViewSet):
    serializer_class = ToDoSerializer

    def get_queryset(self):
        if self.action == "list":
            return ToDo.templates.all().prefetch_related("content").order_by("id")
        return ToDo.objects.all().prefetch_related("content").order_by("id")

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk):
        obj = self.get_object()
        obj.pk = None
        obj.save()
        for i in ToDo.objects.get(pk=pk).content.all():
            obj.content.add(i)
        return Response()
