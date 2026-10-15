from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from .models import Event
from .forms import EventForm


class HomeView(TemplateView):
    template_name = "events/home.html"


class EventListView(ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(is_deleted=False)


class EventDetailView(DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.filter(is_deleted=False)


class EventSoftDeleteView(View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, is_deleted=False)
        event.soft_delete()
        return redirect("events:event_list")


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = "/events/"


class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = "/events/"
