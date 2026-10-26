# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import sqlite3

import pytest

from tasktracker.db import get_db


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute("SELECT 1")

    assert "closed" in str(e.value)


def test_foreign_keys_enabled(app):
    with app.app_context():
        assert get_db().execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_table_columns(app):
    with app.app_context():
        db = get_db()
        users = [row["name"] for row in db.execute("PRAGMA table_info(users)")]
        tasks = [row["name"] for row in db.execute("PRAGMA table_info(tasks)")]

    assert users == ["id", "username", "password_hash"]
    assert tasks == ["id", "user_id", "title", "description", "is_complete"]


def test_task_defaults(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO tasks (user_id, title) VALUES (1, 'Defaults task')")
        task = db.execute("SELECT * FROM tasks WHERE title = 'Defaults task'").fetchone()

    assert task["user_id"] == 1
    assert task["description"] == ""
    assert task["is_complete"] == 0


def test_is_complete_must_be_0_or_1(app):
    with app.app_context():
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            db.execute("UPDATE tasks SET is_complete = 2 WHERE id = 1")


def test_task_requires_existing_user(app):
    with app.app_context():
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            db.execute("INSERT INTO tasks (user_id, title) VALUES (999, 'Orphan task')")


def test_cannot_delete_user_who_has_tasks(app):
    # User 1 owns a task in tests/data.sql
    with app.app_context():
        db = get_db()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            db.execute("DELETE FROM users WHERE id = 1")


def test_init_db_command(app, runner):
    # tests/data.sql already saved users and tasks, so check init-db clears them
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM tasks").fetchone()[0] > 0

    result = runner.invoke(args=["init-db"])
    assert result.exit_code == 0
    assert "Initialized the database" in result.output

    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
