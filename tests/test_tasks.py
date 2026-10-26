# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import pytest
from markupsafe import escape

from tasktracker.db import get_db

# In tests/data.sql, task 1 belongs to the "test" user and task 2 to "other"
OWN_TASK_TITLE = "Finish the INF601 project"
OTHER_TASK_TITLE = "Other user private task"


def get_task_row(app, task_id):
    with app.app_context():
        return get_db().execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()


def count_tasks(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM tasks").fetchone()[0]


def page_text(message):
    """A message as it appears in the HTML, after Jinja escapes it."""
    return str(escape(message)).encode()


# --- Login protection ---

@pytest.mark.parametrize("path", ("/tasks/", "/tasks/new", "/tasks/1/edit"))
def test_pages_require_login(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize("path", (
    "/tasks/new", "/tasks/1/edit", "/tasks/1/toggle", "/tasks/1/delete",
))
def test_actions_require_login(client, app, path):
    response = client.post(path, data={"title": "Sneaky"})
    assert response.headers["Location"] == "/auth/login"

    # Nothing was added, changed, or deleted
    assert count_tasks(app) == 2
    task = get_task_row(app, 1)
    assert task["title"] == OWN_TASK_TITLE
    assert task["is_complete"] == 0


@pytest.mark.parametrize("path", ("/tasks/1/toggle", "/tasks/1/delete"))
def test_actions_reject_get(client, auth, app, path):
    auth.login()
    assert client.get(path).status_code == 405

    task = get_task_row(app, 1)
    assert task is not None
    assert task["is_complete"] == 0


# --- Dashboard ---

def test_dashboard_shows_only_own_tasks(client, auth):
    auth.login()
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert OWN_TASK_TITLE.encode() in response.data
    assert OTHER_TASK_TITLE.encode() not in response.data
    assert b"You have completed 0 of 1 tasks." in response.data

    auth.login("other", "other-password")
    response = client.get("/tasks/")
    assert OTHER_TASK_TITLE.encode() in response.data
    assert OWN_TASK_TITLE.encode() not in response.data


# --- Add Task ---

def test_new_task(client, auth, app):
    auth.login()
    assert client.get("/tasks/new").status_code == 200

    response = client.post("/tasks/new", data={
        "title": "  Buy milk  ",
        "description": "2%\r\nFrom the corner store",
    })
    assert response.headers["Location"] == "/tasks/"

    task = get_task_row(app, 3)
    assert task["user_id"] == 1
    assert task["title"] == "Buy milk"
    assert task["description"] == "2%\nFrom the corner store"
    assert task["is_complete"] == 0

    response = client.get("/tasks/")
    assert page_text('Task "Buy milk" added.') in response.data


def test_new_task_ignores_user_id_in_form(client, auth, app):
    auth.login()
    client.post("/tasks/new", data={"title": "Mine", "user_id": "2"})
    assert get_task_row(app, 3)["user_id"] == 1


@pytest.mark.parametrize(("title", "description", "message"), (
    ("", "", b"Title is required."),
    ("   ", "", b"Title is required."),
    ("a" * 101, "", b"Title must be 100 characters or fewer."),
    ("Valid title", "d" * 1001, b"Description must be 1000 characters or fewer."),
))
def test_new_task_validate_input(client, auth, app, title, description, message):
    auth.login()
    response = client.post("/tasks/new", data={"title": title, "description": description})
    assert response.status_code == 200
    assert message in response.data
    assert count_tasks(app) == 2


def test_new_task_allows_max_lengths(client, auth, app):
    auth.login()
    # 1001 characters as sent, but the \r\n line break counts as one character
    description = "d" * 499 + "\r\n" + "d" * 500
    client.post("/tasks/new", data={"title": "a" * 100, "description": description})
    assert count_tasks(app) == 3


def test_new_task_keeps_input_after_error(client, auth):
    auth.login()
    response = client.post("/tasks/new", data={"title": "", "description": "Keep me"})
    assert b"Keep me" in response.data


# --- Edit Task ---

def test_edit_task(client, auth, app):
    auth.login()
    response = client.get("/tasks/1/edit")
    assert response.status_code == 200
    assert f'value="{OWN_TASK_TITLE}"'.encode() in response.data

    response = client.post("/tasks/1/edit", data={
        "title": "Updated title",
        "description": "New details",
        "is_complete": "1",
    })
    assert response.headers["Location"] == "/tasks/"

    task = get_task_row(app, 1)
    assert task["title"] == "Updated title"
    assert task["description"] == "New details"
    assert task["is_complete"] == 1
    assert task["user_id"] == 1

    response = client.get("/tasks/")
    assert page_text('Task "Updated title" updated.') in response.data


def test_edit_unchecked_box_marks_not_complete(client, auth, app):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE tasks SET is_complete = 1 WHERE id = 1")
        db.commit()

    auth.login()
    response = client.get("/tasks/1/edit")
    assert b"checked" in response.data

    client.post("/tasks/1/edit", data={"title": OWN_TASK_TITLE})
    assert get_task_row(app, 1)["is_complete"] == 0


@pytest.mark.parametrize(("title", "message"), (
    ("", b"Title is required."),
    ("a" * 101, b"Title must be 100 characters or fewer."),
))
def test_edit_task_validate_input(client, auth, app, title, message):
    auth.login()
    response = client.post("/tasks/1/edit", data={"title": title, "description": "Changed"})
    assert response.status_code == 200
    assert message in response.data

    # Nothing was saved, and the form shows what the user typed
    task = get_task_row(app, 1)
    assert task["title"] == OWN_TASK_TITLE
    assert task["description"] == "Belongs to the test user"
    assert b"Changed" in response.data


def test_edit_ignores_user_id_in_form(client, auth, app):
    auth.login()
    client.post("/tasks/1/edit", data={"title": "Still mine", "user_id": "2"})
    assert get_task_row(app, 1)["user_id"] == 1


# --- Complete and delete ---

def test_toggle_task(client, auth, app):
    auth.login()

    response = client.post("/tasks/1/toggle")
    assert response.headers["Location"] == "/tasks/"
    assert get_task_row(app, 1)["is_complete"] == 1
    response = client.get("/tasks/")
    assert page_text(f'Task "{OWN_TASK_TITLE}" marked complete.') in response.data
    assert b"Mark not complete" in response.data

    client.post("/tasks/1/toggle")
    assert get_task_row(app, 1)["is_complete"] == 0
    response = client.get("/tasks/")
    assert page_text(f'Task "{OWN_TASK_TITLE}" marked not complete.') in response.data


def test_delete_task(client, auth, app):
    auth.login()

    response = client.post("/tasks/1/delete")
    assert response.headers["Location"] == "/tasks/"
    assert get_task_row(app, 1) is None

    response = client.get("/tasks/")
    assert page_text(f'Task "{OWN_TASK_TITLE}" deleted.') in response.data
    assert b"You don't have any tasks yet." in response.data


# --- Ownership ---

@pytest.mark.parametrize(("method", "path"), (
    ("GET", "/tasks/2/edit"),
    ("POST", "/tasks/2/edit"),
    ("POST", "/tasks/2/toggle"),
    ("POST", "/tasks/2/delete"),
))
def test_cannot_touch_other_users_task(client, auth, app, method, path):
    auth.login()
    response = client.open(path, method=method, data={"title": "Hijacked"})
    assert response.status_code == 404
    assert OTHER_TASK_TITLE.encode() not in response.data

    # The other user's task is unchanged
    task = get_task_row(app, 2)
    assert task["title"] == OTHER_TASK_TITLE
    assert task["is_complete"] == 0


@pytest.mark.parametrize(("method", "path"), (
    ("GET", "/tasks/999/edit"),
    ("POST", "/tasks/999/toggle"),
    ("POST", "/tasks/999/delete"),
))
def test_missing_task_is_404(client, auth, method, path):
    auth.login()
    assert client.open(path, method=method).status_code == 404


# --- Safe handling of user input ---

def test_task_title_is_escaped(client, auth):
    auth.login()
    client.post("/tasks/new", data={"title": "<script>alert(1)</script>"})
    response = client.get("/tasks/")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in response.data


def test_sql_in_title_is_stored_as_plain_text(client, auth, app):
    # Parameterized queries pass this to SQLite as data, never as SQL
    title = "Robert'); DROP TABLE tasks;--"
    auth.login()
    client.post("/tasks/new", data={"title": title})
    assert get_task_row(app, 3)["title"] == title
    assert count_tasks(app) == 3
