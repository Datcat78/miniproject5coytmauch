# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import os

import pytest

from tasktracker import create_app
from tasktracker.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app(tmp_path):
    """Create an app that uses a fresh temporary database for each test."""
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app


@pytest.fixture
def client(app):
    """A test client for making requests without running the server."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A runner for calling the app's Flask CLI commands."""
    return app.test_cli_runner()


class AuthActions:
    """Log the test client in and out."""

    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test-password"):
        return self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
