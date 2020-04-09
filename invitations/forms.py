from django.forms import ModelForm

from invitations.models import Event


class EventForm(ModelForm):

    class Meta:
        model = Event
        fields = ['organizer', 'occasion', 'date', 'location']
