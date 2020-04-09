from django.shortcuts import render
from django.views.generic import FormView

from invitations.forms import EventForm


class EventCreateView(FormView):
    form_class = EventForm
    template_name = 'invitations/event.html'
