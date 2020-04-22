from django.contrib import admin

from invitations.models import Event, EventAttendee, EventTask, Person

admin.site.register(Person)
admin.site.register(Event)
admin.site.register(EventAttendee)
admin.site.register(EventTask)
