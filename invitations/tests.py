import pytest
from django.urls import reverse

class TestEventView:

    def test_get(self, client):
        url = reverse('invitations:event_create')
        res = client.get(url)
        assert res.status_code == 200

