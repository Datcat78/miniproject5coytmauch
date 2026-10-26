# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest

from tasktracker import create_app
from tasktracker.db import init_db


@pytest.fixture
def app(tmp_path):
    """Create an app that uses a fresh temporary database for each test."""
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
    })

    with app.app_context():
        init_db()

    yield app


@pytest.fixture
def client(app):
    """A test client for making requests without running the server."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A runner for calling the app's Flask CLI commands."""
    return app.test_cli_runner()
