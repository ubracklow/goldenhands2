from django.forms import DateTimeField, ModelForm, formset_factory

from invitations.models import Event, EventTask, Person


class EventForm(ModelForm):
    date = DateTimeField(input_formats=["%d/%m/%Y %H:%M"])

    class Meta:
        model = Event
        fields = ["date", "occasion", "location"]


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ["name", "email"]


PersonFormSet = formset_factory(PersonForm, extra=5)


class EventTaskForm(ModelForm):
    class Meta:
        model = EventTask
        fields = [
            "task",
        ]

    def __init__(self, *args, **kwargs):
        event_pk = kwargs.pop("event")
        self.event = Event.objects.get(pk=event_pk)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if self.cleaned_data == {}:
            return
        instance = super().save(commit=False)
        instance.event = self.event
        instance.save()
        return instance


EventTaskFormSet = formset_factory(EventTaskForm, extra=5)
