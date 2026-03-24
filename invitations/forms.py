from typing import Any, cast

from crispy_forms.bootstrap import PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.forms import CharField, DateTimeField, EmailInput, ModelForm, TextInput, formset_factory
from django.utils.safestring import mark_safe

from invitations.models import Event, EventTask, Person
from invitations.widgets import LocationAutocompleteWidget


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ["name", "email"]
        widgets = {
            "name": TextInput(attrs={"class": "form-control", "placeholder": "Name"}),
            "email": EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
        }

    helper = FormHelper()
    helper.form_tag = False
    helper.form_class = "form-horizontal"
    helper.label_class = "col-sm-3"
    helper.field_class = "col-sm-7"


PersonFormSet = formset_factory(PersonForm, extra=2)


class EventForm(ModelForm):
    date = DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=TextInput(attrs={"placeholder": "DD/MM/YYYY HH:mm"}),
    )
    location = CharField(widget=LocationAutocompleteWidget())

    class Meta:
        model = Event
        fields = ["date", "occasion", "location"]

    helper = FormHelper()
    helper.form_tag = False
    helper.form_class = "form-horizontal"
    helper.label_class = "col-sm-3"
    helper.field_class = "col-sm-7"
    helper.layout = Layout(
        PrependedText("date", mark_safe('<span class="glyphicon glyphicon-calendar"></span>')),
        "occasion",
        "location",
    )


class EventTaskForm(ModelForm):
    class Meta:
        model = EventTask
        fields = ["task"]
        widgets = {
            "task": TextInput(),
        }

    helper = FormHelper()
    helper.form_tag = False
    helper.form_class = "form-horizontal"
    helper.label_class = "col-sm-3"
    helper.field_class = "col-sm-7"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        event_pk: int = kwargs.pop("event")
        self.event: Event = Event.objects.get(pk=event_pk)
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> EventTask | None:
        if self.cleaned_data == {}:
            return None
        instance = cast(EventTask, super().save(commit=False))
        instance.event = self.event
        instance.save()
        return instance


EventTaskFormSet = formset_factory(EventTaskForm, extra=2)
