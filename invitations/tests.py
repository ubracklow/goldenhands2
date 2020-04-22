import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from invitations.models import Event, EventAttendee, EventTask, Person
from invitations.views import FinalView


@pytest.mark.django_db
class TestModels:
    def setup(self):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, attendee=person1)
        EventAttendee.objects.create(event=self.event, attendee=person2)
        EventTask.objects.create(event=self.event, task="Wine")
        EventTask.objects.create(event=self.event, task="Chocolate Cake")

    def test_assign_attendee_tasks_even_numbers(self):
        self.event.assign_attendee_tasks()
        for t in EventTask.objects.all():
            assert t.attendee
        attendees = EventAttendee.objects.values_list("attendee__name")
        assignments = EventTask.objects.values_list("attendee__attendee__name")
        for a in attendees:
            assert a in assignments

    def test_assign_attendees_outnumber_tasks(self):
        person3 = Person.objects.create(name="Judith", email="another@mail.com")
        EventAttendee.objects.create(event=self.event, attendee=person3)
        self.event.assign_attendee_tasks()
        for t in EventTask.objects.all():
            assert t.attendee

    def test_assign_tasks_outnumber_attendees(self):
        EventTask.objects.create(event=self.event, task="Salad")
        self.event.assign_attendee_tasks()
        for t in EventTask.objects.all():
            assert t.attendee


class TestStartView:
    def test_get(self, client):
        url = reverse("invitations:start")
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:organizer_create") in res.rendered_content


@pytest.mark.django_db
class TestOrganizerView:
    def test_post(self, client):
        assert len(Person.objects.all()) == 0
        url = reverse("invitations:organizer_create")
        res = client.post(url, data={"name": "Ute", "email": "me@foo.com"})
        assert res.status_code == 302
        assert len(Person.objects.all()) == 1
        organizer = Person.objects.first()
        assert res.url == reverse(
            "invitations:event_create", kwargs={"pk": organizer.pk}
        )


@pytest.mark.django_db
class TestEventView:
    def test_post_sets_organizer(self, client):
        assert len(Event.objects.all()) == 0
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        url = reverse("invitations:event_create", kwargs={"pk": organizer.pk})
        data = {
            "occasion": "Poker night",
            "date": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "location": "my house",
        }
        res = client.post(url, data=data)
        event = Event.objects.first()
        assert res.status_code == 302
        assert res.url == reverse(
            "invitations:event_add_attendee", kwargs={"pk": event.pk}
        )
        assert event.organizer == organizer


@pytest.mark.django_db
class TestAttendeeView:
    def test_post_creates_person_and_attendee(self, client):
        assert len(Person.objects.all()) == 0
        assert len(EventAttendee.objects.all()) == 0
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        url = reverse("invitations:event_add_attendee", kwargs={"pk": event.pk})
        res = client.get(url)
        assert res.status_code == 200
        name = "My Guest"
        email = "foo@bar.com"
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-name": name,
            "form-0-email": email,
            "form-1-name": name,
            "form-1-email": email,
            "form-2-name": "",
            "form-2-email": "",
        }
        response = client.post(url, data)
        assert len(Person.objects.all()) == 3
        attendees = EventAttendee.objects.all()
        assert len(attendees) == 2
        for a in attendees:
            assert a.event == event
        assert response.url == reverse(
            "invitations:event_add_task", kwargs={"pk": event.pk}
        )


@pytest.mark.django_db
class TestEventTaskView:
    def test_post_creates_tasks(self, client):
        assert len(EventTask.objects.all()) == 0
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=event, attendee=person1)
        EventAttendee.objects.create(event=event, attendee=person2)
        url = reverse("invitations:event_add_task", kwargs={"pk": event.pk})
        res = client.get(url)
        assert res.status_code == 200
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-task": "Wine",
            "form-1-task": "Chocolate Cake",
            "form-2-task": "",
        }
        response = client.post(url, data)
        tasks = EventTask.objects.all()
        assert len(tasks) == 2
        for t in tasks:
            assert t.event == event
            assert t.attendee
        assert response.url == reverse(
            "invitations:event_invite", kwargs={"pk": event.pk}
        )


@pytest.mark.django_db
class TestInviteView:
    def setup(self):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, attendee=person1)
        EventAttendee.objects.create(event=self.event, attendee=person2)
        EventTask.objects.create(event=self.event, task="Wine")
        EventTask.objects.create(event=self.event, task="Chocolate Cake")

    def test_get_even_numbers_guests_and_tasks(self, client):
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert self.event.organizer.name in response.rendered_content
        for a in self.event.eventattendee_set.all():
            assert a.attendee.name in response.rendered_content
        for t in self.event.eventtask_set.all():
            assert t.task in response.rendered_content
        assert (
            reverse("invitations:event_final", kwargs={"pk": self.event.pk})
            in response.rendered_content
        )

    def test_get_attendees_outnumber_tasks(self, client):
        person3 = Person.objects.create(name="Judith", email="another@mail.com")
        EventAttendee.objects.create(event=self.event, attendee=person3)
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert self.event.organizer.name in response.rendered_content
        for a in self.event.eventattendee_set.all():
            assert a.attendee.name in response.rendered_content
        for t in self.event.eventtask_set.all():
            assert t.task in response.rendered_content

    def test_get_tasks_outnumber_attendees(self, client):
        EventTask.objects.create(event=self.event, task="Salad")
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert self.event.organizer.name in response.rendered_content
        for a in self.event.eventattendee_set.all():
            assert a.attendee.name in response.rendered_content
        for t in self.event.eventtask_set.all():
            assert t.task in response.rendered_content


@pytest.mark.django_db
class TestFinalView:
    def setup(self):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, attendee=person1)
        EventAttendee.objects.create(event=self.event, attendee=person2)
        EventTask.objects.create(event=self.event, task="Wine")
        EventTask.objects.create(event=self.event, task="Chocolate Cake")
        self.event.assign_attendee_tasks()

    def test_send_email(self):
        view = FinalView()
        view.event = self.event
        view.send_email()
        email = mail.outbox[0]
        assert self.event.organizer.email in email.to
        assert self.event.organizer.email in email.body
        for a in self.event.eventattendee_set.all():
            assert a.attendee.email in email.to
            assert a.attendee.name in email.body

    def test_get_sends_email(self, client):
        url = reverse("invitations:event_final", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert self.event.occasion in res.rendered_content
        assert len(mail.outbox) == 1
