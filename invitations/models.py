import random

from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} {self.email}"


class Event(models.Model):
    organizer = models.ForeignKey(Person, on_delete=models.CASCADE)
    occasion = models.TextField()
    date = models.DateTimeField()
    location = models.TextField()

    def __str__(self):
        return f"{self.organizer.name} - {self.occasion}"

    def assign_attendee_tasks(self):
        tasks = list(self.eventtask_set.all())
        attendees = list(self.eventattendee_set.all())
        while len(attendees) < len(tasks):
            attendees.append(random.choice(attendees))
        for a in attendees:
            if tasks:
                task = random.choice(tasks)
                task.attendee = a
                task.save()
                tasks.remove(task)


class EventAttendee(models.Model):
    attendee = models.ForeignKey(Person, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.attendee_id} - {self.event.occasion}"


class EventTask(models.Model):
    task = models.CharField(max_length=255)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    attendee = models.ForeignKey(
        EventAttendee, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return f"{self.task} - {self.event.pk}"
