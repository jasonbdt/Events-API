import time
import pytest
import requests

BASE_URL = "http://localhost:5001"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


def _unique_username(prefix="user"):
    return f"{prefix}_{int(time.time() * 1000)}"


def _register_and_login(base_url, prefix="user"):
    """Register a fresh user, log in, return (username, token)."""
    username = _unique_username(prefix)
    password = "Test1234!"

    resp = requests.post(f"{base_url}/api/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, f"Registration failed: {resp.text}"

    resp = requests.post(f"{base_url}/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"

    token = resp.json()["access_token"]
    return username, token


@pytest.fixture()
def auth_token(base_url):
    """Registers a new user and returns a valid JWT access token."""
    _, token = _register_and_login(base_url)
    return token


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
