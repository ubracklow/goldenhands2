from django.urls import path

from invitations.views import (
    AttendeeView,
    EventCreateView,
    EventEditView,
    FinalView,
    InviteView,
    OrganizerEditView,
    OrganizerView,
    StartView,
    TaskView,
    add_attendee_form,
    add_task_form,
)

app_name = "invitations"
urlpatterns = [
    path("", StartView.as_view(), name="start"),
    path("organizer/add", OrganizerView.as_view(), name="organizer_create"),
    path("organizer/<int:pk>/edit/", OrganizerEditView.as_view(), name="organizer_edit"),
    path(
        "organizer/<int:pk>/add_event/", EventCreateView.as_view(), name="event_create"
    ),
    path("event/<int:pk>/edit_event/", EventEditView.as_view(), name="event_edit"),
    path(
        "event/<int:pk>/add_attendee/",
        AttendeeView.as_view(),
        name="event_add_attendee",
    ),
    path("event/<int:pk>/add_task/", TaskView.as_view(), name="event_add_task"),
    path("add_attendee_form/", add_attendee_form, name="add_attendee_form"),
    path("event/<int:pk>/add_task_form/", add_task_form, name="add_task_form"),
    path("event/<int:pk>/invite/", InviteView.as_view(), name="event_invite"),
    path("event/<int:pk>/final/", FinalView.as_view(), name="event_final"),
]
