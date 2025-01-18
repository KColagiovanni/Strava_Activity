import pytest
from strava_activity_package import app

@pytest.fixture
def client():
    client = app.test_client()

    yield client