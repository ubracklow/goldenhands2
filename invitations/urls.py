from django.urls import path

from invitations.views import (
    AttendeeView,
    EventCreateView,
    FinalView,
    InviteView,
    OrganizerView,
    StartView,
    TaskView,
)

app_name = "invitations"
urlpatterns = [
    path("", StartView.as_view(), name="start"),
    path("organizer/add", OrganizerView.as_view(), name="organizer_create"),
    path(
        "organizer/<int:pk>/add_event/", EventCreateView.as_view(), name="event_create"
    ),
    path(
        "event/<int:pk>/add_attendee/",
        AttendeeView.as_view(),
        name="event_add_attendee",
    ),
    path("event/<int:pk>/add_task/", TaskView.as_view(), name="event_add_task"),
    path("event/<int:pk>/invite/", InviteView.as_view(), name="event_invite"),
    path("event/<int:pk>/final/", FinalView.as_view(), name="event_final"),
]
