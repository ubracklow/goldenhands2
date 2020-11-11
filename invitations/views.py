from bootstrap_datepicker_plus import DateTimePickerInput
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from invitations.forms import EventForm, EventTaskFormSet, PersonFormSet
from invitations.models import Event, EventAttendee, Person


class StartView(TemplateView):
    template_name = "invitations/start.html"


class OrganizerView(CreateView):
    template_name = "invitations/organizer.html"
    model = Person
    fields = ["name", "email"]

    def get_success_url(self):
        return reverse_lazy("invitations:event_create", kwargs={"pk": self.object.pk})


class EventCreateView(CreateView):
    template_name = "invitations/event.html"
    form_class = EventForm

    def get_form(self):
        form = super().get_form()
        form.fields["date"].widget = DateTimePickerInput(format="%d/%m/%Y %H:%M")
        return form

    def form_valid(self, form):
        form.instance.organizer = Person.objects.get(pk=self.kwargs["pk"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "invitations:event_add_attendee", kwargs={"pk": self.object.pk}
        )


class AttendeeView(FormView):
    template_name = "invitations/attendee.html"
    model = Person
    form_class = PersonFormSet
    event = None

    def form_valid(self, form):
        self.event = Event.objects.get(pk=self.kwargs["pk"])
        for data in form.cleaned_data:
            if data != {}:
                person = Person.objects.create(name=data["name"], email=data["email"])
                EventAttendee.objects.create(attendee=person, event=self.event)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("invitations:event_add_task", kwargs={"pk": self.event.pk})


class TaskView(FormView):
    template_name = "invitations/task.html"
    form_class = EventTaskFormSet

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {"event": self.kwargs["pk"]}
        return kwargs

    def form_valid(self, form):
        for f in form:
            f.save()
        event = Event.objects.get(pk=self.kwargs["pk"])
        event.assign_attendee_tasks()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "invitations:event_invite", kwargs={"pk": self.kwargs["pk"]}
        )


class EmailMixin:
    def get_email_context(self, context, event):
        context["event"] = event
        tasks = event.eventtask_set.all()
        attendees = event.eventattendee_set.all()
        if len(tasks) >= len(attendees):
            context["even_or_task_outnumber"] = True
            context["tasks"] = tasks
        else:
            attendees = attendees.exclude(
                attendee_id__in=tasks.values_list("attendee__attendee_id")
            )
            context["tasks"] = tasks
            context["attendees_without_task"] = attendees
        return context


class InviteView(EmailMixin, TemplateView):
    template_name = "invitations/invite.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = Event.objects.get(pk=self.kwargs["pk"])
        context = self.get_email_context(context, event)
        return context


class FinalView(EmailMixin, TemplateView):
    template_name = "invitations/final.html"
    event = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.event = Event.objects.get(pk=self.kwargs["pk"])
        context["event"] = self.event
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.send_email()
        return response

    def send_email(self):
        context = self.get_email_context({}, self.event)
        text_content = render_to_string("invitations/invite_email.txt", context)
        html_content = render_to_string("invitations/invite_email.html", context)
        recipients = [
            self.event.organizer.email,
        ]
        for a in self.event.eventattendee_set.all():
            recipients.append(a.attendee.email)
        email = EmailMultiAlternatives("An invitation for you", text_content)
        email.attach_alternative(html_content, "text/html")
        email.to = recipients
        email.send()
