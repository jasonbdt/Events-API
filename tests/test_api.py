import time
import requests
import pytest
from tests.conftest import BASE_URL, _register_and_login, _unique_username


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_healthy(base_url):
    resp = requests.get(f"{base_url}/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_user_creates_new_user(base_url):
    username = _unique_username("reg")
    resp = requests.post(f"{base_url}/api/auth/register", json={"username": username, "password": "Pass1234!"})

    assert resp.status_code == 201
    body = resp.json()
    assert "user" in body
    assert body["user"]["username"] == username
    assert "id" in body["user"]
    # Password must never leak
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_username_returns_400(base_url):
    username = _unique_username("dup")
    payload = {"username": username, "password": "Pass1234!"}
    requests.post(f"{base_url}/api/auth/register", json=payload)

    resp = requests.post(f"{base_url}/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_register_missing_fields_returns_400(base_url):
    resp = requests.post(f"{base_url}/api/auth/register", json={"username": "only_name"})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_returns_jwt_token(base_url):
    username = _unique_username("login")
    password = "Secure99!"
    requests.post(f"{base_url}/api/auth/register", json={"username": username, "password": password})

    resp = requests.post(f"{base_url}/api/auth/login", json={"username": username, "password": password})

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    # Token must be a non-empty string
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20
    assert body["user"]["username"] == username


def test_login_wrong_password_returns_401(base_url):
    username = _unique_username("badpw")
    requests.post(f"{base_url}/api/auth/register", json={"username": username, "password": "Right1!"})

    resp = requests.post(f"{base_url}/api/auth/login", json={"username": username, "password": "Wrong1!"})
    assert resp.status_code == 401


def test_login_unknown_user_returns_401(base_url):
    resp = requests.post(f"{base_url}/api/auth/login", json={"username": "ghost_xyz_999", "password": "any"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Events — create
# ---------------------------------------------------------------------------

def test_create_public_event_requires_auth_and_succeeds_with_token(base_url, auth_headers):
    payload = {
        "title": "Integration Test Event",
        "date": "2027-09-01T18:00:00",
        "location": "Test Arena",
        "description": "Created by integration test",
        "is_public": True,
    }
    resp = requests.post(f"{base_url}/api/events", json=payload, headers=auth_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == payload["title"]
    assert body["location"] == payload["location"]
    assert body["is_public"] is True
    assert "id" in body


def test_create_event_without_token_returns_401(base_url):
    payload = {"title": "No Auth Event", "date": "2027-10-01T10:00:00"}
    resp = requests.post(f"{base_url}/api/events", json=payload)
    assert resp.status_code == 401


def test_create_event_missing_date_returns_400(base_url, auth_headers):
    resp = requests.post(f"{base_url}/api/events", json={"title": "No Date"}, headers=auth_headers)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Events — list / get
# ---------------------------------------------------------------------------

def test_list_events_returns_200(base_url):
    resp = requests.get(f"{base_url}/api/events")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_nonexistent_event_returns_404(base_url):
    resp = requests.get(f"{base_url}/api/events/999999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# RSVP — public event
# ---------------------------------------------------------------------------

def _create_public_event(base_url, headers):
    """Helper: create a public event and return its id."""
    payload = {
        "title": f"RSVP Test Event {int(time.time() * 1000)}",
        "date": "2027-11-15T19:00:00",
        "is_public": True,
    }
    resp = requests.post(f"{base_url}/api/events", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_rsvp_to_public_event_returns_201(base_url, auth_headers):
    event_id = _create_public_event(base_url, auth_headers)

    resp = requests.post(f"{base_url}/api/rsvps/event/{event_id}", json={"attending": True}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["event_id"] == event_id
    assert body["attending"] is True


def test_rsvp_update_existing_returns_200(base_url, auth_headers):
    event_id = _create_public_event(base_url, auth_headers)

    # First RSVP
    requests.post(f"{base_url}/api/rsvps/event/{event_id}", json={"attending": True}, headers=auth_headers)
    # Update it
    resp = requests.post(f"{base_url}/api/rsvps/event/{event_id}", json={"attending": False}, headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["attending"] is False


def test_get_rsvps_for_event(base_url, auth_headers):
    event_id = _create_public_event(base_url, auth_headers)
    requests.post(f"{base_url}/api/rsvps/event/{event_id}", json={"attending": True}, headers=auth_headers)

    resp = requests.get(f"{base_url}/api/rsvps/event/{event_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "rsvps" in body
    assert "stats" in body
    assert body["stats"]["attending"] >= 1
