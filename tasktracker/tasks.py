# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for
)

from .auth import login_required
from .db import get_db

bp = Blueprint("tasks", __name__, url_prefix="/tasks")

# Task form rules (new.html and edit.html show the same limits to the user)
TITLE_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 1000


def get_task(task_id):
    """Return the task with this id, but only if it belongs to the logged-in user.

    A task that doesn't exist and a task owned by someone else both give a 404,
    so users can't even find out which task ids belong to other people.
    """
    task = get_db().execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, g.user["id"]),
    ).fetchone()

    if task is None:
        abort(404, "Task not found.")

    return task


def validate_task_form():
    """Read the title and description from the submitted form.

    Returns (title, description, errors), where errors is a list of messages
    to show the user. An empty list means the data is safe to save.
    """
    title = request.form.get("title", "").strip()
    # Browsers send line breaks as \r\n; store them as \n so lengths match
    # what the user saw in the textarea
    description = request.form.get("description", "").replace("\r\n", "\n").strip()
    errors = []

    if not title:
        errors.append("Title is required.")
    elif len(title) > TITLE_MAX_LENGTH:
        errors.append(f"Title must be {TITLE_MAX_LENGTH} characters or fewer.")

    if len(description) > DESCRIPTION_MAX_LENGTH:
        errors.append(f"Description must be {DESCRIPTION_MAX_LENGTH} characters or fewer.")

    return title, description, errors


@bp.route("/")
@login_required
def dashboard():
    """List the logged-in user's tasks, and only theirs."""
    tasks = get_db().execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY is_complete, id",
        (g.user["id"],),
    ).fetchall()
    completed_count = sum(task["is_complete"] for task in tasks)
    return render_template(
        "tasks/dashboard.html", tasks=tasks, completed_count=completed_count
    )


@bp.route("/new", methods=("GET", "POST"))
@login_required
def new():
    """Show the Add Task form, and save the new task when it's submitted."""
    if request.method == "POST":
        title, description, errors = validate_task_form()

        if not errors:
            db = get_db()
            # user_id comes from the session, never from the form
            db.execute(
                "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
                (g.user["id"], title, description),
            )
            db.commit()
            flash(f'Task "{title}" added.', "success")
            return redirect(url_for("tasks.dashboard"))

        for error in errors:
            flash(error, "error")

    return render_template("tasks/new.html")


@bp.route("/<int:task_id>/edit", methods=("GET", "POST"))
@login_required
def edit(task_id):
    """Show the Edit Task form, and save the changes when it's submitted."""
    task = get_task(task_id)

    if request.method == "POST":
        title, description, errors = validate_task_form()
        # An unchecked checkbox isn't sent at all
        is_complete = 1 if "is_complete" in request.form else 0

        if not errors:
            db = get_db()
            db.execute(
                "UPDATE tasks SET title = ?, description = ?, is_complete = ?"
                " WHERE id = ? AND user_id = ?",
                (title, description, is_complete, task_id, g.user["id"]),
            )
            db.commit()
            flash(f'Task "{title}" updated.', "success")
            return redirect(url_for("tasks.dashboard"))

        for error in errors:
            flash(error, "error")

    return render_template("tasks/edit.html", task=task)


@bp.route("/<int:task_id>/toggle", methods=("POST",))
@login_required
def toggle(task_id):
    """Mark a task complete, or mark a completed task not complete."""
    task = get_task(task_id)
    is_complete = 0 if task["is_complete"] else 1

    db = get_db()
    db.execute(
        "UPDATE tasks SET is_complete = ? WHERE id = ? AND user_id = ?",
        (is_complete, task_id, g.user["id"]),
    )
    db.commit()

    status = "complete" if is_complete else "not complete"
    flash(f'Task "{task["title"]}" marked {status}.', "success")
    return redirect(url_for("tasks.dashboard"))


@bp.route("/<int:task_id>/delete", methods=("POST",))
@login_required
def delete(task_id):
    """Delete a task."""
    task = get_task(task_id)

    db = get_db()
    db.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, g.user["id"]),
    )
    db.commit()

    flash(f'Task "{task["title"]}" deleted.', "success")
    return redirect(url_for("tasks.dashboard"))
