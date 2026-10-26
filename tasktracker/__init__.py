# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import os

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException


def create_app(test_config=None):
    """Application factory: create and configure the Task Tracker app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # The secret key signs the session cookie. "dev" is a development-only
        # fallback: set the SECRET_KEY environment variable to a long random
        # value anywhere the app is actually deployed.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "tasktracker.sqlite"),
        # Don't send the session cookie with form posts from other websites
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Make sure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """Show errors like 404 Not Found inside the site's base layout."""
        # Start from Werkzeug's response to keep its headers (a 405 lists the
        # allowed methods), then swap in our page
        response = error.get_response()
        response.data = render_template("error.html", error=error)
        response.content_type = "text/html; charset=utf-8"
        return response

    # Database connection cleanup and the "flask init-db" command
    from . import db

    db.init_app(app)

    # Blueprints for the account pages and the private task pages
    from . import auth, tasks

    app.register_blueprint(auth.bp)
    app.register_blueprint(tasks.bp)

    return app
