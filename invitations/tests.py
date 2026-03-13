import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from invitations.models import Event, EventAttendee, EventTask, Person
from invitations.views import FinalView


@pytest.mark.django_db
class TestModels:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, person=person1)
        EventAttendee.objects.create(event=self.event, person=person2)
        EventTask.objects.create(event=self.event, task="Wine")
        EventTask.objects.create(event=self.event, task="Chocolate Cake")

    def test_assign_attendee_tasks_even_numbers(self):
        self.event.assign_attendee_tasks()
        for t in EventTask.objects.all():
            assert t.attendee
        attendees = EventAttendee.objects.values_list("person__name")
        assignments = EventTask.objects.values_list("attendee__person__name")
        for a in attendees:
            assert a in assignments

    def test_assign_attendees_outnumber_tasks(self):
        person3 = Person.objects.create(name="Judith", email="another@mail.com")
        EventAttendee.objects.create(event=self.event, person=person3)
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
class TestOrganizerEditView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        self.organizer = Person.objects.create(name="Ute", email="my@mail.com")
        self.event = Event.objects.create(
            organizer=self.organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )

    def test_get_prefills_form(self, client):
        url = reverse("invitations:organizer_edit", kwargs={"pk": self.organizer.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert self.organizer.name in res.rendered_content
        assert self.organizer.email in res.rendered_content

    def test_post_updates_person(self, client):
        url = reverse("invitations:organizer_edit", kwargs={"pk": self.organizer.pk})
        client.post(url, data={"name": "Updated Name", "email": "new@mail.com"})
        assert Person.objects.count() == 1
        self.organizer.refresh_from_db()
        assert self.organizer.name == "Updated Name"
        assert self.organizer.email == "new@mail.com"

    def test_redirects_to_event_edit_when_event_exists(self, client):
        url = reverse("invitations:organizer_edit", kwargs={"pk": self.organizer.pk})
        res = client.post(url, data={"name": "Ute", "email": "my@mail.com"})
        assert res.status_code == 302
        assert res.url == reverse("invitations:event_edit", kwargs={"pk": self.event.pk})

    def test_redirects_to_event_create_when_no_event(self, client):
        self.event.delete()
        url = reverse("invitations:organizer_edit", kwargs={"pk": self.organizer.pk})
        res = client.post(url, data={"name": "Ute", "email": "my@mail.com"})
        assert res.status_code == 302
        assert res.url == reverse("invitations:event_create", kwargs={"pk": self.organizer.pk})


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

    def test_has_back_button(self, client):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        url = reverse("invitations:event_create", kwargs={"pk": organizer.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:organizer_edit", kwargs={"pk": organizer.pk}) in res.rendered_content


@pytest.mark.django_db
class TestEventEditView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        self.organizer = Person.objects.create(name="Ute", email="my@mail.com")
        self.event = Event.objects.create(
            organizer=self.organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )

    def test_get_prefills_form(self, client):
        url = reverse("invitations:event_edit", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert self.event.occasion in res.rendered_content
        assert self.event.location in res.rendered_content

    def test_post_updates_event(self, client):
        url = reverse("invitations:event_edit", kwargs={"pk": self.event.pk})
        data = {
            "occasion": "Updated Occasion",
            "date": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "location": "New Location",
        }
        client.post(url, data=data)
        assert Event.objects.count() == 1
        self.event.refresh_from_db()
        assert self.event.occasion == "Updated Occasion"
        assert self.event.location == "New Location"

    def test_redirects_to_add_attendee(self, client):
        url = reverse("invitations:event_edit", kwargs={"pk": self.event.pk})
        data = {
            "occasion": "Foo",
            "date": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "location": "Bar",
        }
        res = client.post(url, data=data)
        assert res.status_code == 302
        assert res.url == reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})

    def test_has_back_button(self, client):
        url = reverse("invitations:event_edit", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:organizer_edit", kwargs={"pk": self.organizer.pk}) in res.rendered_content


@pytest.mark.django_db
class TestAttendeeView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        self.organizer = Person.objects.create(name="Ute", email="my@mail.com")
        self.event = Event.objects.create(
            organizer=self.organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )

    def test_post_creates_person_and_attendee(self, client):
        assert len(Person.objects.all()) == 1
        assert len(EventAttendee.objects.all()) == 0
        url = reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})
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
            assert a.event == self.event
        assert response.url == reverse(
            "invitations:event_add_task", kwargs={"pk": self.event.pk}
        )

    def test_get_prefills_existing_attendees(self, client):
        person1 = Person.objects.create(name="Thea", email="thea@mail.com")
        EventAttendee.objects.create(event=self.event, person=person1)
        url = reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert "Thea" in res.rendered_content
        assert "thea@mail.com" in res.rendered_content

    def test_post_replaces_attendees(self, client):
        person1 = Person.objects.create(name="Thea", email="thea@mail.com")
        EventAttendee.objects.create(event=self.event, person=person1)
        url = reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-name": "NewGuest",
            "form-0-email": "new@mail.com",
        }
        client.post(url, data)
        assert EventAttendee.objects.count() == 1
        assert EventAttendee.objects.first().person.name == "NewGuest"
        assert not Person.objects.filter(name="Thea").exists()

    def test_post_preserves_tasks_with_null_attendee(self, client):
        person1 = Person.objects.create(name="Thea", email="thea@mail.com")
        ea = EventAttendee.objects.create(event=self.event, person=person1)
        task = EventTask.objects.create(event=self.event, task="Wine", attendee=ea)
        url = reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-name": "NewGuest",
            "form-0-email": "new@mail.com",
        }
        client.post(url, data)
        task.refresh_from_db()
        assert EventTask.objects.filter(pk=task.pk).exists()
        assert task.attendee is None

    def test_has_back_button(self, client):
        url = reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:event_edit", kwargs={"pk": self.event.pk}) in res.rendered_content


@pytest.mark.django_db
class TestEventTaskView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        self.organizer = Person.objects.create(name="Ute", email="my@mail.com")
        self.person1 = Person.objects.create(name="Thea", email="your@mail.com")
        self.person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=self.organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, person=self.person1)
        EventAttendee.objects.create(event=self.event, person=self.person2)

    def test_post_creates_tasks(self, client):
        assert len(EventTask.objects.all()) == 0
        url = reverse("invitations:event_add_task", kwargs={"pk": self.event.pk})
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
            assert t.event == self.event
            assert t.attendee
        assert response.url == reverse(
            "invitations:event_invite", kwargs={"pk": self.event.pk}
        )

    def test_get_prefills_existing_tasks(self, client):
        EventTask.objects.create(event=self.event, task="Wine")
        url = reverse("invitations:event_add_task", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert "Wine" in res.rendered_content

    def test_post_replaces_tasks(self, client):
        EventTask.objects.create(event=self.event, task="Wine")
        url = reverse("invitations:event_add_task", kwargs={"pk": self.event.pk})
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-task": "Cake",
        }
        client.post(url, data)
        assert EventTask.objects.count() == 1
        assert EventTask.objects.first().task == "Cake"

    def test_has_back_button(self, client):
        url = reverse("invitations:event_add_task", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:event_add_attendee", kwargs={"pk": self.event.pk}) in res.rendered_content


@pytest.mark.django_db
class TestInviteView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, person=person1)
        EventAttendee.objects.create(event=self.event, person=person2)
        EventTask.objects.create(event=self.event, task="Wine")
        EventTask.objects.create(event=self.event, task="Chocolate Cake")

    def test_get_even_numbers_guests_and_tasks(self, client):
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert self.event.organizer.name in response.rendered_content
        for a in self.event.eventattendee_set.all():
            assert a.person.name in response.rendered_content
        for t in self.event.eventtask_set.all():
            assert t.task in response.rendered_content
        assert (
            reverse("invitations:event_final", kwargs={"pk": self.event.pk})
            in response.rendered_content
        )

    def test_get_attendees_outnumber_tasks(self, client):
        person3 = Person.objects.create(name="Judith", email="another@mail.com")
        EventAttendee.objects.create(event=self.event, person=person3)
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert self.event.organizer.name in response.rendered_content
        for a in self.event.eventattendee_set.all():
            assert a.person.name in response.rendered_content
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
            assert a.person.name in response.rendered_content
        for t in self.event.eventtask_set.all():
            assert t.task in response.rendered_content

    def test_has_back_button(self, client):
        self.event.assign_attendee_tasks()
        url = reverse("invitations:event_invite", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert reverse("invitations:event_add_task", kwargs={"pk": self.event.pk}) in res.rendered_content


class TestAddAttendeeFormView:
    def test_returns_form_row_for_given_index(self, client):
        url = reverse("invitations:add_attendee_form")
        res = client.get(url, {"form-TOTAL_FORMS": "2"})
        assert res.status_code == 200
        assert 'name="form-2-name"' in res.content.decode()
        assert 'name="form-2-email"' in res.content.decode()

    def test_updates_total_forms_counter(self, client):
        url = reverse("invitations:add_attendee_form")
        res = client.get(url, {"form-TOTAL_FORMS": "2"})
        assert 'value="3"' in res.content.decode()

    def test_label_shows_correct_row_number(self, client):
        url = reverse("invitations:add_attendee_form")
        res = client.get(url, {"form-TOTAL_FORMS": "4"})
        assert "5." in res.content.decode()

    def test_defaults_to_index_zero_when_no_total_given(self, client):
        url = reverse("invitations:add_attendee_form")
        res = client.get(url)
        assert res.status_code == 200
        assert 'name="form-0-name"' in res.content.decode()


@pytest.mark.django_db
class TestAddTaskFormView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )

    def test_returns_form_row_for_given_index(self, client):
        url = reverse("invitations:add_task_form", kwargs={"pk": self.event.pk})
        res = client.get(url, {"form-TOTAL_FORMS": "2"})
        assert res.status_code == 200
        assert 'name="form-2-task"' in res.content.decode()

    def test_updates_total_forms_counter(self, client):
        url = reverse("invitations:add_task_form", kwargs={"pk": self.event.pk})
        res = client.get(url, {"form-TOTAL_FORMS": "2"})
        assert 'value="3"' in res.content.decode()

    def test_label_is_rendered(self, client):
        url = reverse("invitations:add_task_form", kwargs={"pk": self.event.pk})
        res = client.get(url, {"form-TOTAL_FORMS": "3"})
        assert "Task" in res.content.decode()

    def test_defaults_to_index_zero_when_no_total_given(self, client):
        url = reverse("invitations:add_task_form", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert res.status_code == 200
        assert 'name="form-0-task"' in res.content.decode()


@pytest.mark.django_db
class TestFinalView:
    @pytest.fixture(autouse=True)
    def _setup_data(self, db):
        organizer = Person.objects.create(name="Ute", email="my@mail.com")
        person1 = Person.objects.create(name="Thea", email="your@mail.com")
        person2 = Person.objects.create(name="Stefan", email="their@mail.com")
        self.event = Event.objects.create(
            organizer=organizer, occasion="Foo", date=timezone.now(), location="Bar"
        )
        EventAttendee.objects.create(event=self.event, person=person1)
        EventAttendee.objects.create(event=self.event, person=person2)
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
            assert a.person.email in email.to
            assert a.person.name in email.body

    def test_get_sends_email(self, client):
        url = reverse("invitations:event_final", kwargs={"pk": self.event.pk})
        res = client.get(url)
        assert self.event.occasion in res.rendered_content
        assert len(mail.outbox) == 1
