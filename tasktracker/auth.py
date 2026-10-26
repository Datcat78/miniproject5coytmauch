# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import functools
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Registration rules (register.html shows the same rules to the user)
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_]+")
PASSWORD_MIN_LENGTH = 8


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Show the registration form, and create the account when it's submitted."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        errors = []

        if not username:
            errors.append("Username is required.")
        elif not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
            errors.append(
                f"Username must be {USERNAME_MIN_LENGTH} to {USERNAME_MAX_LENGTH} characters long."
            )
        elif not USERNAME_PATTERN.fullmatch(username):
            errors.append("Username can only contain letters, numbers, and underscores.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        if not errors:
            db = get_db()
            try:
                # Store only the salted hash, never the password itself
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                # The UNIQUE constraint on users.username rejected a duplicate
                errors.append(f"Username {username} is already taken.")
            else:
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("auth.login"))

        for error in errors:
            flash(error, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Show the login form, and log the user in when it's submitted."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error = None
        user = None

        if not username or not password:
            error = "Username and password are required."
        else:
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            # Same message either way, so the login form doesn't confirm
            # which usernames exist
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Incorrect username or password."

        if error is None:
            # Start a fresh session that remembers only who is logged in
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("tasks.dashboard"))

        flash(error, "error")

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    """Before every request, look up the logged-in user and store them in g.user."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        # Leave out password_hash so it can't end up in a template by accident
        g.user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()


@bp.route("/logout")
def logout():
    """Forget the logged-in user and go back to the home page."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


def login_required(view):
    """Decorator for views that need a logged-in user; redirects others to login."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to see that page.", "info")
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
