# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

from flask import Blueprint, abort, g, render_template

from .auth import login_required
from .db import get_db

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


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


@bp.route("/")
@login_required
def dashboard():
    """List the logged-in user's tasks, and only theirs."""
    tasks = get_db().execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY is_complete, id",
        (g.user["id"],),
    ).fetchall()
    return render_template("tasks/dashboard.html", tasks=tasks)


@bp.route("/new")
@login_required
def new():
    # Placeholder: creating tasks will be added with task management
    return render_template("tasks/new.html")


@bp.route("/<int:task_id>/edit")
@login_required
def edit(task_id):
    task = get_task(task_id)
    # Placeholder: saving changes will be added with task management
    return render_template("tasks/edit.html", task=task)
