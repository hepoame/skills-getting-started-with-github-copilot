from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as api


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(api, "activities", deepcopy(api.activities))
    return TestClient(api.app)


def test_root_redirects_to_static_index(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data_without_caching(client: TestClient) -> None:
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == api.activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client: TestClient) -> None:
    activity_name = "Basketball Club"
    email = "student@mergington.edu"

    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in api.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client: TestClient) -> None:
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_rejects_unknown_activity(client: TestClient) -> None:
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client: TestClient) -> None:
    response = client.post("/activities/Basketball%20Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client: TestClient) -> None:
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in api.activities[activity_name]["participants"]


def test_unregister_rejects_unregistered_participant(client: TestClient) -> None:
    response = client.delete(
        "/activities/Basketball%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )


def test_unregister_rejects_unknown_activity(client: TestClient) -> None:
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
