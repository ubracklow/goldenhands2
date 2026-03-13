import pytest


@pytest.fixture(autouse=True)
def use_simple_staticfiles(settings):
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
