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

