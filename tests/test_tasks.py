# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest


@pytest.mark.parametrize("path", ("/tasks/", "/tasks/new", "/tasks/1/edit"))
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"


def test_dashboard_shows_only_own_tasks(client, auth):
    auth.login()
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert b"Finish the INF601 project" in response.data
    assert b"Other user private task" not in response.data

    auth.login("other", "other-password")
    response = client.get("/tasks/")
    assert b"Other user private task" in response.data
    assert b"Finish the INF601 project" not in response.data


def test_new_task_page(client, auth):
    auth.login()
    assert client.get("/tasks/new").status_code == 200


def test_edit_own_task(client, auth):
    auth.login()
    response = client.get("/tasks/1/edit")
    assert response.status_code == 200
    assert b"Finish the INF601 project" in response.data


@pytest.mark.parametrize("path", (
    "/tasks/2/edit",    # belongs to the other user
    "/tasks/999/edit",  # doesn't exist
))
def test_cannot_open_other_users_or_missing_task(client, auth, path):
    auth.login()
    response = client.get(path)
    assert response.status_code == 404
    assert b"Other user private task" not in response.data
