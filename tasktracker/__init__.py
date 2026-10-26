# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import os

from flask import Flask, render_template


def create_app(test_config=None):
    """Application factory: create and configure the Task Tracker app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # "dev" is only for local development; override it in instance/config.py
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "tasktracker.sqlite"),
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

    # Blueprints for the account and task pages (routes are added in later steps)
    from . import auth, tasks

    app.register_blueprint(auth.bp)
    app.register_blueprint(tasks.bp)

    return app
