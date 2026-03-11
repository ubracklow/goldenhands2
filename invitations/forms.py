from django.forms import CharField, DateTimeField, EmailInput, ModelForm, TextInput, formset_factory

from invitations.models import Event, EventTask, Person
from invitations.widgets import LocationAutocompleteWidget


class EventForm(ModelForm):
    date = DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=TextInput(attrs={"class": "form-control", "placeholder": "DD/MM/YYYY HH:mm"}),
    )
    location = CharField(widget=LocationAutocompleteWidget(attrs={"class": "form-control"}))

    class Meta:
        model = Event
        fields = ["date", "occasion", "location"]
        widgets = {
            "occasion": TextInput(attrs={"class": "form-control"}),
        }


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ["name", "email"]
        widgets = {
            "name": TextInput(attrs={"class": "form-control", "placeholder": "Name"}),
            "email": EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
        }


PersonFormSet = formset_factory(PersonForm, extra=5)


class EventTaskForm(ModelForm):
    class Meta:
        model = EventTask
        fields = [
            "task",
        ]
        widgets = {
            "task": TextInput(attrs={"class": "form-control"}),
        }

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
