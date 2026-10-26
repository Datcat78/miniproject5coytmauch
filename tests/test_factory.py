# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest

from tasktracker import create_app


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_secret_key_defaults_to_dev(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert create_app({"TESTING": True}).config["SECRET_KEY"] == "dev"


def test_secret_key_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "key-from-environment")
    assert create_app({"TESTING": True}).config["SECRET_KEY"] == "key-from-environment"


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Task Tracker" in response.data


def test_about(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"INF601" in response.data


def assert_uses_base_layout(response):
    """Check for parts of the page that only come from base.html."""
    assert b'href="/static/style.css"' in response.data
    assert b"<nav>" in response.data
    assert b"<footer>INF601 Mini Project 5" in response.data


@pytest.mark.parametrize(("path", "title"), (
    ("/", "Home"),
    ("/about", "About"),
    ("/auth/register", "Register"),
    ("/auth/login", "Log In"),
    ("/tasks/", "Dashboard"),
    ("/tasks/new", "Add Task"),
    ("/tasks/1/edit", "Edit Task"),
))
def test_every_page_uses_base_layout(client, auth, path, title):
    auth.login()
    response = client.get(path)
    assert response.status_code == 200
    assert f"<title>{title} - Task Tracker</title>".encode() in response.data
    assert_uses_base_layout(response)


def test_error_page_uses_base_layout(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert b"<title>404 Not Found - Task Tracker</title>" in response.data
    assert_uses_base_layout(response)


def test_405_error_keeps_allow_header(client):
    response = client.get("/auth/logout")
    assert response.status_code == 405
    assert "POST" in response.headers["Allow"]
    assert_uses_base_layout(response)
