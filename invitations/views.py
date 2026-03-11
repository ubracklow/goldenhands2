from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from invitations.forms import EventForm, EventTaskForm, EventTaskFormSet, PersonForm, PersonFormSet
from invitations.models import Event, EventAttendee, Person


class StartView(TemplateView):
    template_name = "invitations/start.html"


class OrganizerFormMixin:
    model = Person
    fields = ["name", "email"]
    template_name = "invitations/organizer.html"


class OrganizerView(OrganizerFormMixin, CreateView):
    def get_success_url(self):
        return reverse_lazy("invitations:event_create", kwargs={"pk": self.object.pk})


class OrganizerEditView(OrganizerFormMixin, UpdateView):
    def get_success_url(self):
        event = Event.objects.filter(organizer=self.object).first()
        if event:
            return reverse_lazy("invitations:event_edit", kwargs={"pk": event.pk})
        return reverse_lazy("invitations:event_create", kwargs={"pk": self.object.pk})


class EventFormMixin:
    form_class = EventForm
    template_name = "invitations/event.html"


class EventCreateView(EventFormMixin, CreateView):
    def form_valid(self, form):
        form.instance.organizer = Person.objects.get(pk=self.kwargs["pk"])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("invitations:organizer_edit", kwargs={"pk": self.kwargs["pk"]})
        return context

    def get_success_url(self):
        return reverse_lazy(
            "invitations:event_add_attendee", kwargs={"pk": self.object.pk}
        )


class EventEditView(EventFormMixin, UpdateView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse("invitations:organizer_edit", kwargs={"pk": self.object.organizer.pk})
        return context

    def get_success_url(self):
        return reverse_lazy(
            "invitations:event_add_attendee", kwargs={"pk": self.object.pk}
        )


class AttendeeView(FormView):
    template_name = "invitations/attendee.html"
    model = Person
    form_class = PersonFormSet
    event = None

    def get_initial(self):
        event = Event.objects.get(pk=self.kwargs["pk"])
        return [
            {"name": ea.person.name, "email": ea.person.email}
            for ea in event.eventattendee_set.select_related("person").all()
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self.kwargs["pk"]
        return context

    def form_valid(self, form):
        self.event = Event.objects.get(pk=self.kwargs["pk"])
        attendee_pks = list(self.event.eventattendee_set.values_list("person_id", flat=True))
        self.event.eventattendee_set.all().delete()
        Person.objects.filter(pk__in=attendee_pks).delete()
        for data in form.cleaned_data:
            if data != {}:
                person = Person.objects.create(name=data["name"], email=data["email"])
                EventAttendee.objects.create(person=person, event=self.event)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("invitations:event_add_task", kwargs={"pk": self.event.pk})


class TaskView(FormView):
    template_name = "invitations/task.html"
    form_class = EventTaskFormSet

    def get_initial(self):
        event = Event.objects.get(pk=self.kwargs["pk"])
        return [{"task": t.task} for t in event.eventtask_set.all()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {"event": self.kwargs["pk"]}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self.kwargs["pk"]
        return context

    def form_valid(self, form):
        event = Event.objects.get(pk=self.kwargs["pk"])
        event.eventtask_set.all().delete()
        for f in form:
            f.save()
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
                person_id__in=tasks.values_list("attendee__person_id")
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
            recipients.append(a.person.email)
        email = EmailMultiAlternatives("An invitation for you", text_content)
        email.attach_alternative(html_content, "text/html")
        email.to = recipients
        email.send()


def add_attendee_form(request):
    """Returns a single attendee form row for htmx-powered dynamic addition.

    Called via htmx GET when the user clicks '+' on the attendee step. Reads
    the current formset size from the `form-TOTAL_FORMS` query parameter
    (included automatically by htmx via hx-include), creates an unbound
    PersonForm at that index, and returns a rendered partial containing the
    new row plus an out-of-band swap to increment the management form counter
    so Django accepts the extra data on POST.
    """
    index = int(request.GET.get("form-TOTAL_FORMS", 0))
    form = PersonForm(prefix=f"form-{index}")
    return render(request, "invitations/_attendee_row.html", {
        "form": form,
        "index": index + 1,
        "new_total": index + 1,
    })


def add_task_form(request, pk):
    """Returns a single task form row for htmx-powered dynamic addition.

    Called via htmx GET when the user clicks '+' on the task step. Reads the
    current formset size from the `form-TOTAL_FORMS` query parameter (included
    automatically by htmx via hx-include), creates an unbound EventTaskForm at
    that index, and returns a rendered partial containing the new row plus an
    out-of-band swap to increment the management form counter so Django accepts
    the extra data on POST. The event pk is required because EventTaskForm
    needs it to save tasks to the correct event.
    """
    index = int(request.GET.get("form-TOTAL_FORMS", 0))
    form = EventTaskForm(prefix=f"form-{index}", event=pk)
    return render(request, "invitations/_task_row.html", {
        "form": form,
        "index": index + 1,
        "new_total": index + 1,
    })


