import pytest
from fastapi.testclient import TestClient
from src.app import app, DEFAULT_ACTIVITIES, activities


@pytest.fixture
def client():
    """
    Provides a TestClient instance with fresh activities data for each test.
    Resets the activities to their original state after each test.
    """
    # Reset activities to default state before test
    activities.clear()
    activities.update({k: {**v, "participants": v["participants"].copy()} for k, v in DEFAULT_ACTIVITIES.items()})
    
    # Provide the test client
    client = TestClient(app)
    yield client
    
    # Reset activities to default state after test
    activities.clear()
    activities.update({k: {**v, "participants": v["participants"].copy()} for k, v in DEFAULT_ACTIVITIES.items()})
