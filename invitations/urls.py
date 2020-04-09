from django.urls import include, path

from invitations.views import EventCreateView


app_name = 'invitations'
urlpatterns = [
    path('event/', EventCreateView.as_view(), name='event_create'),
]
