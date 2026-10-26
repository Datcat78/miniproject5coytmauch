# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest

from tasktracker import create_app


@pytest.fixture
def app():
    """Create an app instance configured for testing."""
    app = create_app({"TESTING": True})
    yield app


@pytest.fixture
def client(app):
    """A test client for making requests without running the server."""
    return app.test_client()
