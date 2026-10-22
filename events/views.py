from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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


<<<<<<< HEAD
class EventSoftDeleteView(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, pk):
        events = Event.objects.filter(is_deleted=False)
        if not request.user.has_perm("events.delete_event"):
            events = events.filter(owner=request.user)
        event = get_object_or_404(events, pk=pk)
        event.soft_delete()
        return redirect("events:event_list")
=======
class OwnerRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.get_object().owner == self.request.user
>>>>>>> upstream/main


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = "/events/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

<<<<<<< HEAD

class EventUpdateView(PermissionRequiredMixin, UpdateView):
=======
class EventUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
>>>>>>> upstream/main
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = "/events/"
    permission_required = "events.change_event"
    login_url = "accounts:login"

    def get_queryset(self):
        return Event.objects.filter(is_deleted=False)
