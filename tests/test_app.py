import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities(monkeypatch):
    test_activities = {
        "Robotics Club": {
            "description": "Build and program robots",
            "schedule": "Mondays, 3:30 PM",
            "max_participants": 3,
            "participants": ["student@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activities):
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_current_activities(client, activities):
    # Arrange
    expected_activities = activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activities):
    # Arrange
    email = "new-student@example.com"

    # Act
    response = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Robotics Club"}
    assert email in activities["Robotics Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, activities):
    # Arrange
    email = "student@example.com"
    participants_before = activities["Robotics Club"]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities["Robotics Club"]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client, activities):
    # Arrange
    participants_before = activities["Robotics Club"]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "new-student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities["Robotics Club"]["participants"] == participants_before


def test_unregister_removes_participant(client, activities):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        "/activities/Robotics%20Club/participants/student%40example.com"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Robotics Club"}
    assert email not in activities["Robotics Club"]["participants"]


def test_unregister_rejects_unknown_activity(client, activities):
    # Arrange
    participants_before = activities["Robotics Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants/student%40example.com"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities["Robotics Club"]["participants"] == participants_before


def test_unregister_rejects_nonparticipant(client, activities):
    # Arrange
    participants_before = activities["Robotics Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Robotics%20Club/participants/other%40example.com"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities["Robotics Club"]["participants"] == participants_before