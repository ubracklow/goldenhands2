from typing import Any

import pytest


@pytest.fixture(autouse=True)
def use_simple_staticfiles(settings: Any) -> None:
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
