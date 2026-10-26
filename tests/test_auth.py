# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest
from flask import g, session
from werkzeug.security import check_password_hash

from tasktracker.db import get_db


def count_users(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]


def test_register(client, app):
    assert client.get("/auth/register").status_code == 200

    response = client.post("/auth/register", data={
        "username": "newuser",
        "password": "new-password",
        "confirm_password": "new-password",
    })
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        user = get_db().execute(
            "SELECT * FROM users WHERE username = 'newuser'"
        ).fetchone()

    assert user is not None
    # Only a hash is stored, never the plaintext password
    assert "new-password" not in user["password_hash"]
    assert check_password_hash(user["password_hash"], "new-password")


def test_register_then_login(client):
    client.post("/auth/register", data={
        "username": "newuser",
        "password": "new-password",
        "confirm_password": "new-password",
    })
    response = client.post(
        "/auth/login", data={"username": "newuser", "password": "new-password"},
        follow_redirects=True,
    )
    assert b"Welcome, newuser." in response.data
    assert b"You don't have any tasks yet." in response.data


@pytest.mark.parametrize(("username", "password", "confirm_password", "message"), (
    ("", "valid-password", "valid-password", b"Username is required."),
    ("ab", "valid-password", "valid-password", b"Username must be 3 to 30 characters long."),
    ("a" * 31, "valid-password", "valid-password", b"Username must be 3 to 30 characters long."),
    ("bad name!", "valid-password", "valid-password",
     b"Username can only contain letters, numbers, and underscores."),
    ("newuser", "", "", b"Password is required."),
    ("newuser", "short", "short", b"Password must be at least 8 characters long."),
    ("newuser", "valid-password", "other-password", b"Passwords do not match."),
    ("test", "valid-password", "valid-password", b"Username test is already taken."),
))
def test_register_validate_input(client, app, username, password, confirm_password, message):
    response = client.post("/auth/register", data={
        "username": username,
        "password": password,
        "confirm_password": confirm_password,
    })
    assert response.status_code == 200
    assert message in response.data
    # No account was created (tests/data.sql has 2 users)
    assert count_users(app) == 2


def test_register_shows_every_error_and_keeps_username(client):
    response = client.post("/auth/register", data={
        "username": "ab", "password": "pw123", "confirm_password": "pw123",
    })
    assert b"Username must be 3 to 30 characters long." in response.data
    assert b"Password must be at least 8 characters long." in response.data
    # The username is filled back in; passwords never are
    assert b'value="ab"' in response.data
    assert b"pw123" not in response.data


def test_register_missing_form_fields(client, app):
    # A request with no fields at all is a validation error, not a crash
    response = client.post("/auth/register", data={})
    assert response.status_code == 200
    assert b"Username is required." in response.data
    assert count_users(app) == 2


def test_login(client, auth):
    assert client.get("/auth/login").status_code == 200

    response = auth.login()
    assert response.headers["Location"] == "/tasks/"

    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["username"] == "test"
        # g.user doesn't carry the password hash into templates
        assert "password_hash" not in g.user.keys()


@pytest.mark.parametrize(("username", "password", "message"), (
    ("nobody", "test-password", b"Incorrect username or password."),
    ("test", "wrong-password", b"Incorrect username or password."),
    ("", "test-password", b"Username and password are required."),
    ("test", "", b"Username and password are required."),
))
def test_login_validate_input(client, auth, username, password, message):
    response = auth.login(username, password)
    assert response.status_code == 200
    assert message in response.data

    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout(client, auth):
    auth.login()

    with client:
        response = auth.logout()
        assert "user_id" not in session

    assert response.headers["Location"] == "/"


def test_nav_links(client, auth):
    response = client.get("/")
    assert b"Log In" in response.data
    assert b"Register" in response.data
    assert b"Log Out" not in response.data

    auth.login()
    response = client.get("/")
    assert b"Log Out" in response.data
    assert b'<span class="nav-user">test</span>' in response.data
    assert b"Log In" not in response.data
